#! /bin/bash

# The name of this program.
progname=`echo "$0" | sed 's%^.*/%%'`
help="Try \`$progname --help' for more information."

# Directory names.
prefix=@prefix@
datadir=@datadir@
pkgdatadir=${datadir}/libtool

# Constants.
PROGRAM=$progname
VERSION=0.2

# Global variables.
configure_top=

while [ "$#" != "0" ]; do
  arg=$1
  case "$arg" in
  --help)
    cat <<EOF
Usage: $progname [OPTION]...

Update config.{sub,guess} scripts of a package.

-c, --configure-top   set top directory holding configure scripts
    --help            display this message and exit
    --version         print version information and exit
EOF
    exit 0
    ;;

  --version)
    echo "$PROGRAM $VERSION"
    exit 0
    ;;

  -c | --configure-top)
    shift
    configure_top="$1"
    ;;

  -*)
    echo "$progname: unrecognized option \`$arg'" 1>&2
    echo "$help" 1>&2
    exit 1
    ;;

  *)
    echo "$progname: too many arguments" 1>&2
    echo "$help" 1>&2
    exit 1
    ;;
  esac
  shift
done

if test -n "$configure_top"; then
  if ! test -d "$configure_top"; then
    echo "$progname: $configure_top directory does not exist" 1>&2
    exit 1
  fi
  cd $configure_top
fi

if ! test -f configure.in && ! test -f configure.ac; then
  if test -f config.sub && test -f config.guess; then
    cp -f $pkgdatadir/config.sub .
    cp -f $pkgdatadir/config.guess .
  fi
  exit 0
fi
exec libtoolize --copy --force
