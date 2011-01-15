%define major	7
%define libname_orig	libltdl
%define libname		%mklibname ltdl %{major}
%define libname_devel	%mklibname -d ltdl

# for the testsuite:
%define _disable_ld_no_undefined 1
%define _disable_ld_as_needed 1

# allow --with bootstrap
%define bootstrap 0
%{?_with_bootstrap: %global bootstrap 1}

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
Version:	2.4
Release:	%mkrel 3
License:	GPL
Group:		Development/Other
URL:		http://www.gnu.org/software/libtool/libtool.html
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

Source:		ftp://ftp.gnu.org/gnu/%{name}/%{name}-%{version}.tar.xz
Source1:	%{SOURCE0}.sig

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

# (cjw) when a library that is produced in the build is also linked against, 
#       make sure that the library in the rpm install dir is used for relinking 
#	even if (an older version of) the lib is installed on the system
Patch0:		relink.patch
#
Patch1:		lib64.patch
Patch2:		ltmain-SED.patch
Patch12:	do-not-link-against-deplibs.patch
Patch13:	drop-ld-no-undefined-for-shared-lib-modules.patch
Patch14:	fix-checking-libltdl-is-installed-installable.patch
# (cjw) do not use CFLAGS when running gcj
Patch16:	libtool-2.2.6-use-gcjflags-for-gcj.patch
# (cjw) in the libltdl install test, use --enable-ltdl-install to make sure 
#       the library is built even if it is installed on the system
Patch17:	libtool-2.2.6b-libltdl-install-test-fix.patch
# (cjw) mdemo-dryrun test may fail because file sizes are incorrect in 'before' 
#       file list
Patch18:	libtool-2.4-dryrun-sleepmore.patch

%ifarch %biarches
BuildRequires:	linux32
%endif
BuildRequires:	automake
Buildrequires:	autoconf
# For test 37 to succeed
Buildrequires:	locales-de
%if ! %{bootstrap}
BuildRequires:	gcc-%{fortran_compiler}
BuildRequires:	gcc-java libgcj-static-devel
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

%prep
%setup -q
%patch0 -p1 -b .relink
%patch1 -p1 -b .lib64
%patch2 -p1 -b .ltmain-SED
%patch12 -p1 -b .overlinking
%patch13 -p1 -b .underlinking
%patch14 -p1
%patch16 -p1 -b .gcj-no-cflags
%patch17 -p1 -b .ignore-system-libltdl
%patch18 -p1 -b .sleepmore

%build
./bootstrap

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
ICECC=no %make check
set +x
echo ====================TESTING END=====================
set -x

popd

%install
rm -fr %{buildroot}
%makeinstall_std -C build-%{_target_cpu}-%{_target_os}

sed -e "s,@prefix@,%{_prefix}," -e "s,@datadir@,%{_datadir}," %{SOURCE2} \
  > %{buildroot}%{_bindir}/cputoolize
chmod 755 %{buildroot}%{_bindir}/cputoolize

# biarch support
%ifarch %biarches
%multiarch_binaries $RPM_BUILD_ROOT%{_bindir}/libtool
install -m 755 build-%{alt_arch}-%{_target_os}/libtool $RPM_BUILD_ROOT%{_bindir}/libtool
linux32 /bin/sh -c '%multiarch_binaries $RPM_BUILD_ROOT%{_bindir}/libtool'
%endif

%clean
rm -fr %{buildroot}

%post base
%_install_info %{name}.info

%preun base
%_remove_install_info %{name}.info

%files
%defattr(-,root,root)
%doc AUTHORS INSTALL NEWS README
%doc THANKS TODO ChangeLog*
%{_bindir}/libtool
%{_mandir}/man1/libtool.1.*
%ifarch %biarches
%define alt_multiarch_bindir %(linux32 /bin/rpm --eval %%multiarch_bindir)
%{multiarch_bindir}
%{alt_multiarch_bindir}
%endif

%files base
%defattr(-,root,root)
%doc AUTHORS INSTALL NEWS README
%doc THANKS TODO ChangeLog*
%{_bindir}/cputoolize
%{_bindir}/libtoolize
%{_mandir}/man1/libtoolize.*
%{_infodir}/libtool.info*
%{_datadir}/libtool
%{_datadir}/aclocal/*.m4

%files -n %{libname}
%defattr(-,root,root)
%doc libltdl/README
%{_libdir}/libltdl.so.%{major}
%{_libdir}/libltdl.so.%{major}.*

%files -n %{libname_devel}
%defattr(-,root,root)
%doc tests/demo
%{_includedir}/*
%{_libdir}/*.a
%{_libdir}/*.so
%{_libdir}/*.la




