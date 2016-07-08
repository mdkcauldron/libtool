%define major	7
%define libname_orig	libltdl
%define libname		%mklibname ltdl %{major}
%define libname_devel	%mklibname -d ltdl
%define staticdevelname %mklibname %{libname_orig} -d -s

# for the testsuite:
%define _disable_ld_no_undefined 1
%define _disable_ld_as_needed 1

# allow --with bootstrap
%define bootstrap 0
%{?_with_bootstrap: %global bootstrap 1}

%define arch_has_java 1
%ifarch %arm %mips
%define arch_has_java 0
%endif
%if %bootstrap
%define arch_has_java 0
%endif

# define biarch platforms
%define biarches x86_64 ppc64 sparc64
%ifarch x86_64
%define alt_arch i586
%endif
%ifarch ppc64
%define alt_arch ppc
%endif
%ifarch sparc64
%define alt_arch sparc
%endif

# define fortran compiler
%define fortran_compiler gfortran

Summary:	The GNU libtool, which simplifies the use of shared libraries
Name:		libtool
Version:	2.4.6
Release:	%mkrel 3
License:	GPLv2+
Group:		Development/Other
URL:		http://www.gnu.org/software/libtool/libtool.html

Source:		ftp://ftp.gnu.org/gnu/%{name}/%{name}-%{version}.tar.xz
Source1:	ftp://ftp.gnu.org/gnu/%{name}/%{name}-%{version}.tar.xz.sig

# deprecated: introduced in July 2003
# (cf http://lists.mandriva.com/cooker-amd64/2003-12/msg00046.php)
# but is not needed anymore since Sept 2003 change in rpm "Make "x86_64" the
# canonical arch on amd64"
#
# since Jan 2009, the script doesn't use --config-only anymore since support
# for --config-only in libtoolize has been dropped
Source2:	libtool-cputoolize.sh

# (Abel) Patches please only modify ltmain.in and don't touch ltmain.sh
# otherwise ltmain.sh will not be regenerated, and patches will be lost

# (cjw) in the libltdl install test, use --enable-ltdl-install to make sure 
#       the library is built even if it is installed on the system
Patch17:	libtool-2.2.6b-libltdl-install-test-fix.patch
# (cjw) mdemo test may fail because file sizes are incorrect in 'before'
#       file list
Patch18:	libtool-2.4-dryrun-sleepmore.patch
# (wally) we are not shipping libltdl.la anymore,
#         patch originaly from Gentoo:
#         https://bugs.gentoo.org/show_bug.cgi?id=293921#c10
Patch19:	libtool-2.4.6-fix-building-without-libltdl.la.patch
# (proyvind) add /lib64 & /usr/lib64 to system library path in order to
#            prevent from being added to rpath
Patch20:	libtool-2.2.10-rpath.patch

BuildRequires:	automake
BuildRequires:	autoconf
BuildRequires:	help2man
# For test 37 to succeed
BuildRequires:	locales-de
%if ! %{bootstrap}
BuildRequires:	gcc-%{fortran_compiler}
%ifarch ia64 %ix86 x86_64
BuildRequires:	quadmath-devel
%endif
%endif
%if %arch_has_java
BuildRequires:	gcc-java 
BuildRequires:	libgcj-static-devel
%endif
Requires:	%{name}-base = %{version}-%{release}

%description
The libtool package contains the GNU libtool, a set of shell scripts
which automatically configure UNIX and UNIX-like architectures to
generically build shared libraries.  Libtool provides a consistent,
portable interface which simplifies the process of using shared
libraries.

If you are developing programs which will use shared libraries, you
should install libtool.

%package base
Group:		Development/C
Summary:	Basic package for %{name}
Requires:	file
# cputoolize uses sed
Requires: 	sed
Requires(post): info-install
Requires(preun): info-install

%description base
The libtool package contains the GNU libtool, a set of shell scripts
which automatically configure UNIX and UNIX-like architectures to
generically build shared libraries.  Libtool provides a consistent,
portable interface which simplifies the process of using shared
libraries.

If you are developing programs which will use shared libraries, you
should install libtool.

%package -n %{libname}
Group:		Development/C
Summary:	Shared library files for libtool
License:	LGPL
Provides:	%{libname_orig} = %{version}-%{release}
# old libextractor wrongly provided its own libltdl:
Conflicts:	%{_lib}extractor1 < 0.5.18a

%description -n %{libname}
Shared library files for libtool DLL library from the libtool package.

%package -n %{libname_devel}
Group:		Development/C
Summary:	Development files for libtool
License:	LGPL
Requires:	%{name} = %{version}
Requires:	%{libname} = %{version}
Provides:	%{libname_orig}-devel = %{version}-%{release}
Provides:	%{name}-devel
Obsoletes:	%{mklibname ltdl 3}-devel

%description -n %{libname_devel}
Development headers, and files for development from the libtool package.

%package -n %{staticdevelname}
Summary: libtldl - static library
Group:   Development/C
Requires:   %{libname} = %{version}-%{release}

%description -n %{staticdevelname}
Static library (.a) version of libtldl.
%prep
%setup -q
%patch17 -p1 -b .ignore-system-libltdl
%patch18 -p1 -b .sleepmore
%patch19 -p1 -b .ltdl.la-fix
%patch20 -p1 -b .rpath~

%build
# don't use configure macro - it forces libtoolize, which is bad -jgarzik
# Use configure macro but define __libtoolize to be /bin/true -Geoff
%define __libtoolize /bin/true
# And don't overwrite config.{sub,guess} in this package as well -- Abel
%define __cputoolize /bin/true

# build alt-arch libtool first
# NOTE: don't bother to make libtool biarch capable within the same
# "binary", use the multiarch facility to dispatch to the right script.
%ifarch %biarches
mkdir -p build-%{alt_arch}-%{_target_os}
pushd    build-%{alt_arch}-%{_target_os}
linux32 ../configure --prefix=%{_prefix} --build=%{alt_arch}-%{_real_vendor}-%{_target_os}%{?_gnu}
linux32 make
popd
%endif

mkdir -p build-%{_target_cpu}-%{_target_os}
pushd    build-%{_target_cpu}-%{_target_os}
CONFIGURE_TOP=.. %configure2_5x
make

# Do not use -nostdlib to build libraries, and so no need to hardcode gcc path (mdvbz#44616)
# (taken from debian, http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=206356)
# ([PIX] this is not done as a patch since the patch would be too big to maintain)
sed -i -e 's/^\(predep_objects\)=.*/\1=""/' \
       -e 's/^\(postdep_objects\)=.*/\1=""/' \
       -e 's/^\(compiler_lib_search_path\)=.*/\1=""/' \
       -e 's:^\(sys_lib_search_path_spec\)=.*:\1="/lib/ /usr/lib/ /usr/X11R6/lib/ /usr/local/lib/":' \
       -e 's/^\(archive_cmds=\".*\) -nostdlib /\1 /' \
       -e 's/^\(archive_expsym_cmds=\".*\) -nostdlib /\1 /' \
       libtool
# should "compiler_lib_search_dirs" be cleaned too?

popd

%check
pushd    build-%{_target_cpu}-%{_target_os}
set +x
echo ====================TESTING=========================
set -x
# all tests must pass here
# disabling icecream since some tests check the output of gcc
ICECC=no %make check VERBOSE=yes | tee make_check.log 2>&1 # || (cat make_check.log && false)
set +x
echo ====================TESTING END=====================
set -x

popd

%install
%makeinstall_std -C build-%{_target_cpu}-%{_target_os}

rm -f %{buildroot}%{_libdir}/*.la

sed -e "s,@prefix@,%{_prefix}," -e "s,@datadir@,%{_datadir}," %{SOURCE2} \
  > %{buildroot}%{_bindir}/cputoolize
chmod 755 %{buildroot}%{_bindir}/cputoolize

# biarch support
%ifarch %biarches
%multiarch_binaries $RPM_BUILD_ROOT%{_bindir}/libtool
install -m 755 build-%{alt_arch}-%{_target_os}/libtool $RPM_BUILD_ROOT%{_bindir}/libtool
linux32 /bin/sh -c '%multiarch_binaries $RPM_BUILD_ROOT%{_bindir}/libtool'
%endif

%post base
%_install_info %{name}.info

%preun base
%_remove_install_info %{name}.info

%files
%doc AUTHORS INSTALL NEWS README
%doc THANKS TODO
%{_bindir}/libtool
%{_mandir}/man1/libtool.1.*
%ifarch %biarches
%define alt_multiarch_bindir %(linux32 /bin/rpm --eval %%multiarch_bindir)
%{multiarch_bindir}
%{alt_multiarch_bindir}
%endif

%files base
%doc AUTHORS INSTALL NEWS README
%doc THANKS TODO
%{_bindir}/cputoolize
%{_bindir}/libtoolize
%{_mandir}/man1/libtoolize.*
%{_infodir}/libtool.info*
%{_datadir}/libtool
%{_datadir}/aclocal/*.m4

%files -n %{libname}
%doc libltdl/README
%{_libdir}/libltdl.so.%{major}
%{_libdir}/libltdl.so.%{major}.*

%files -n %{libname_devel}
%{_includedir}/*
%{_libdir}/*.so

%files -n %{staticdevelname}
%{_libdir}/*.a
