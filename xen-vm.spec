%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

# Hypervisor ABI
%define hv_abi  4.2

%{!?version: %define version %(cat version)}
%{!?rel: %define rel %(cat rel)}

%define _sourcedir %(pwd)

Summary: Xen is a virtual machine monitor
Name:    xen-qubes-vm
Version: %{version}
Release: %{rel}%{?dist}
Epoch:   2001
Group:   Development/Libraries
License: GPLv2+ and LGPLv2+ and BSD
URL:     http://xen.org/
Source0: xen-%{version}.tar.gz

Source98: apply-patches
Source99: series-vm.conf
Source100: patches.fedora
Source102: patches.misc
Source103: patches.qubes

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: transfig libidn-devel zlib-devel texi2html SDL-devel curl-devel
BuildRequires: libX11-devel python-devel ghostscript texlive-latex
%if "%dist" >= ".fc18"
BuildRequires: texlive-times texlive-courier texlive-helvetic texlive-ntgclass
%endif
BuildRequires: ncurses-devel gtk2-devel libaio-devel
# for the docs
BuildRequires: perl perl(Pod::Man) perl(Pod::Text) texinfo graphviz
# so that the makefile knows to install udev rules
BuildRequires: udev
BuildRequires: gettext
BuildRequires: gnutls-devel
BuildRequires: openssl-devel
# Several tools now use uuid
BuildRequires: libuuid-devel
BuildRequires: which
BuildRequires: autoconf automake
Requires: bridge-utils
Requires: python-lxml
Requires: udev >= 059
Requires: chkconfig
ExclusiveArch: %{ix86} x86_64 ia64
#ExclusiveArch: %{ix86} x86_64 ia64 noarch

Provides: xen-qubes-vm-essentials = %{version}-%{release}
Obsoletes: xen-qubes-vm-essentials < 2001:4.1.2-25
Requires: xen-qubes-vm-libs = %{epoch}:%{version}-%{release}

%define _sourcedir %(pwd)

%description
Just a few xenstore-* tools and Xen hotplug scripts needed by Qubes VMs (including netvm)

%package libs
Summary: Libraries for Xen tools
Group: Development/Libraries
Requires(pre): /sbin/ldconfig
Requires(post): /sbin/ldconfig
Obsoletes: xen-libs < 2001:4.1.2-25
Provides: xen-libs = %{version}-%{release}

%description libs
This package contains the libraries needed to run Xen tools inside of Qubes VM

%package devel
Summary: Development libraries for Xen tools
Group: Development/Libraries
Requires: xen-qubes-vm-libs = %{version}-%{release}
Provides: xen-devel = %{version}-%{release}

%description devel
This package contains what's needed to develop applications
which manage Xen virtual machines.


%package licenses
Summary: License files from Xen source
Group: Documentation

%description licenses
This package contains the license files from the source used
to build the xen packages.

%prep
%setup -q -n xen-%{version}

# Apply patches
%{SOURCE98} %{SOURCE99} %{_sourcedir}

%build
export XEN_VENDORVERSION="-%{release}"
export CFLAGS="$RPM_OPT_FLAGS"
export OCAML_TOOLS=n
export PYTHON=/usr/bin/python
export PYTHON_PATH=/usr/bin/python
autoreconf
./configure --libdir=%{_libdir}
make %{?_smp_mflags} prefix=/usr dist-tools

%install
rm -rf %{buildroot}
export OCAML_TOOLS=n
make DESTDIR=%{buildroot} prefix=/usr install-tools

############ debug packaging: list files ############

find %{buildroot} -print | xargs ls -ld | sed -e 's|.*%{buildroot}||' > f1.list

############ kill unwanted stuff ############

# stubdom: newlib
rm -rf %{buildroot}/usr/*-xen-elf

# hypervisor symlinks
rm -rf %{buildroot}/boot/xen-4.2.gz
rm -rf %{buildroot}/boot/xen-4.gz

# silly doc dir fun
rm -fr %{buildroot}%{_datadir}/doc/xen
rm -rf %{buildroot}%{_datadir}/doc/qemu

# Pointless helper
rm -f %{buildroot}%{_sbindir}/xen-python-path

# qemu stuff (unused or available from upstream)
rm -rf %{buildroot}/usr/share/xen/man

# README's not intended for end users
rm -f %{buildroot}/%{_sysconfdir}/xen/README*

# standard gnu info files
rm -rf %{buildroot}/usr/info

# adhere to Static Library Packaging Guidelines
rm -rf %{buildroot}/%{_libdir}/*.a

# not used in Qubes VM
rm -f %{buildroot}/usr/sbin/xenstored
rm -f %{buildroot}/usr/share/xen/create.dtd
rm -rf %{buildroot}/etc/sysconfig
rm -rf %{buildroot}/etc/rc.d/init.d

############ fixup files in /etc ############

# udev
#rm -rf %{buildroot}/etc/udev/rules.d/xen*.rules
#mv %{buildroot}/etc/udev/xen*.rules %{buildroot}/etc/udev/rules.d
rm -f %{buildroot}/etc/udev/rules.d/xend.rules

# config file only used for hotplug, Fedora uses udev instead
rm -f %{buildroot}/%{_sysconfdir}/sysconfig/xend

############ debug packaging: list files ############

find %{buildroot} -print | xargs ls -ld | sed -e 's|.*%{buildroot}||' > f2.list
diff -u f1.list f2.list || true

############ assemble license files ############

mkdir licensedir
# avoid licensedir to avoid recursion, also stubdom/ioemu and dist
# which are copies of files elsewhere
find . -path licensedir -prune -o -path stubdom/ioemu -prune -o \
  -path dist -prune -o -name COPYING -o -name LICENSE | while read file; do
  mkdir -p licensedir/`dirname $file`
  install -m 644 $file licensedir/$file
done

############ all done now ############

%post -n xen-qubes-vm-libs -p /sbin/ldconfig
%postun -n xen-qubes-vm-libs -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files libs
%defattr(-,root,root)
%{_libdir}/*.so.*

%files

%{_bindir}/xenstore
%{_bindir}/xenstore-*

# Hotplug rules
%config(noreplace) %{_sysconfdir}/udev/rules.d/xen-backend.rules

%dir %attr(0700,root,root) %{_sysconfdir}/xen
%dir %attr(0700,root,root) %{_sysconfdir}/xen/scripts/
%config %attr(0700,root,root) %{_sysconfdir}/xen/scripts/*

# General Xen state
%dir %{_localstatedir}/lib/xen
%dir %{_localstatedir}/lib/xen/dump

# Xen logfiles
%dir %attr(0700,root,root) %{_localstatedir}/log/xen

# Python modules
%dir %{python_sitearch}/xen
%{python_sitearch}/xen/__init__.*
%{python_sitearch}/xen/lowlevel

%{python_sitearch}/xen/util
%{python_sitearch}/xen-*.egg-info

%files devel
%defattr(-,root,root)
%{_includedir}/*.h
%dir %{_includedir}/xen
%{_includedir}/xen/*
%dir %{_includedir}/xenstore-compat
%{_includedir}/xenstore-compat/*
%{_libdir}/*.so

%files licenses
%defattr(-,root,root)
%doc licensedir/*

### XXX: TEMP: Added for xen-vgt test
/etc/bash_completion.d/xl.sh
/etc/xen/cpupool
/etc/xen/xend-config.sxp
/etc/xen/xend-pci-permissive.sxp
/etc/xen/xend-pci-quirks.sxp
/etc/xen/xl.conf
/etc/xen/xlexample.hvm
/etc/xen/xlexample.pvlinux
/etc/xen/xm-config.xml
/etc/xen/xmexample.hvm
/etc/xen/xmexample.hvm-stubdom
/etc/xen/xmexample.nbd
/etc/xen/xmexample.pv-grub
/etc/xen/xmexample.vti
/etc/xen/xmexample1
/etc/xen/xmexample2
/etc/xen/xmexample3
/usr/bin/pygrub
/usr/bin/qemu-img-xen
/usr/bin/qemu-nbd-xen
/usr/bin/remus
/usr/bin/xen-detect
/usr/bin/xencons
/usr/bin/xencov_split
/usr/bin/xentrace
/usr/bin/xentrace_format
/usr/bin/xentrace_setsize
/usr/etc/qemu/target-x86_64.conf
/usr/lib/xen/bin/qemu-dm
/usr/lib/xen/bin/qemu-ga
/usr/lib/xen/bin/qemu-img
/usr/lib/xen/bin/qemu-io
/usr/lib/xen/bin/qemu-nbd
/usr/lib/xen/bin/qemu-system-i386
/usr/lib/xen/bin/xenpaging
/usr/lib/xen/boot/hvmloader
/usr/lib64/fs/ext2fs-lib/fsimage.so
/usr/lib64/fs/fat/fsimage.so
/usr/lib64/fs/iso9660/fsimage.so
/usr/lib64/fs/reiserfs/fsimage.so
/usr/lib64/fs/ufs/fsimage.so
/usr/lib64/fs/xfs/fsimage.so
/usr/lib64/fs/zfs/fsimage.so
/usr/lib64/python2.7/site-packages/fsimage.so
/usr/lib64/python2.7/site-packages/grub/ExtLinuxConf.py
/usr/lib64/python2.7/site-packages/grub/ExtLinuxConf.pyc
/usr/lib64/python2.7/site-packages/grub/ExtLinuxConf.pyo
/usr/lib64/python2.7/site-packages/grub/GrubConf.py
/usr/lib64/python2.7/site-packages/grub/GrubConf.pyc
/usr/lib64/python2.7/site-packages/grub/GrubConf.pyo
/usr/lib64/python2.7/site-packages/grub/LiloConf.py
/usr/lib64/python2.7/site-packages/grub/LiloConf.pyc
/usr/lib64/python2.7/site-packages/grub/LiloConf.pyo
/usr/lib64/python2.7/site-packages/grub/__init__.py
/usr/lib64/python2.7/site-packages/grub/__init__.pyc
/usr/lib64/python2.7/site-packages/grub/__init__.pyo
/usr/lib64/python2.7/site-packages/pygrub-0.3-py2.7.egg-info
/usr/lib64/python2.7/site-packages/xen/remus/__init__.py
/usr/lib64/python2.7/site-packages/xen/remus/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/remus/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/remus/blkdev.py
/usr/lib64/python2.7/site-packages/xen/remus/blkdev.pyc
/usr/lib64/python2.7/site-packages/xen/remus/blkdev.pyo
/usr/lib64/python2.7/site-packages/xen/remus/device.py
/usr/lib64/python2.7/site-packages/xen/remus/device.pyc
/usr/lib64/python2.7/site-packages/xen/remus/device.pyo
/usr/lib64/python2.7/site-packages/xen/remus/image.py
/usr/lib64/python2.7/site-packages/xen/remus/image.pyc
/usr/lib64/python2.7/site-packages/xen/remus/image.pyo
/usr/lib64/python2.7/site-packages/xen/remus/netlink.py
/usr/lib64/python2.7/site-packages/xen/remus/netlink.pyc
/usr/lib64/python2.7/site-packages/xen/remus/netlink.pyo
/usr/lib64/python2.7/site-packages/xen/remus/profile.py
/usr/lib64/python2.7/site-packages/xen/remus/profile.pyc
/usr/lib64/python2.7/site-packages/xen/remus/profile.pyo
/usr/lib64/python2.7/site-packages/xen/remus/qdisc.py
/usr/lib64/python2.7/site-packages/xen/remus/qdisc.pyc
/usr/lib64/python2.7/site-packages/xen/remus/qdisc.pyo
/usr/lib64/python2.7/site-packages/xen/remus/save.py
/usr/lib64/python2.7/site-packages/xen/remus/save.pyc
/usr/lib64/python2.7/site-packages/xen/remus/save.pyo
/usr/lib64/python2.7/site-packages/xen/remus/tapdisk.py
/usr/lib64/python2.7/site-packages/xen/remus/tapdisk.pyc
/usr/lib64/python2.7/site-packages/xen/remus/tapdisk.pyo
/usr/lib64/python2.7/site-packages/xen/remus/util.py
/usr/lib64/python2.7/site-packages/xen/remus/util.pyc
/usr/lib64/python2.7/site-packages/xen/remus/util.pyo
/usr/lib64/python2.7/site-packages/xen/remus/vbd.py
/usr/lib64/python2.7/site-packages/xen/remus/vbd.pyc
/usr/lib64/python2.7/site-packages/xen/remus/vbd.pyo
/usr/lib64/python2.7/site-packages/xen/remus/vdi.py
/usr/lib64/python2.7/site-packages/xen/remus/vdi.pyc
/usr/lib64/python2.7/site-packages/xen/remus/vdi.pyo
/usr/lib64/python2.7/site-packages/xen/remus/vif.py
/usr/lib64/python2.7/site-packages/xen/remus/vif.pyc
/usr/lib64/python2.7/site-packages/xen/remus/vif.pyo
/usr/lib64/python2.7/site-packages/xen/remus/vm.py
/usr/lib64/python2.7/site-packages/xen/remus/vm.pyc
/usr/lib64/python2.7/site-packages/xen/remus/vm.pyo
/usr/lib64/python2.7/site-packages/xen/sv/CreateDomain.py
/usr/lib64/python2.7/site-packages/xen/sv/CreateDomain.pyc
/usr/lib64/python2.7/site-packages/xen/sv/CreateDomain.pyo
/usr/lib64/python2.7/site-packages/xen/sv/DomInfo.py
/usr/lib64/python2.7/site-packages/xen/sv/DomInfo.pyc
/usr/lib64/python2.7/site-packages/xen/sv/DomInfo.pyo
/usr/lib64/python2.7/site-packages/xen/sv/GenTabbed.py
/usr/lib64/python2.7/site-packages/xen/sv/GenTabbed.pyc
/usr/lib64/python2.7/site-packages/xen/sv/GenTabbed.pyo
/usr/lib64/python2.7/site-packages/xen/sv/HTMLBase.py
/usr/lib64/python2.7/site-packages/xen/sv/HTMLBase.pyc
/usr/lib64/python2.7/site-packages/xen/sv/HTMLBase.pyo
/usr/lib64/python2.7/site-packages/xen/sv/Main.py
/usr/lib64/python2.7/site-packages/xen/sv/Main.pyc
/usr/lib64/python2.7/site-packages/xen/sv/Main.pyo
/usr/lib64/python2.7/site-packages/xen/sv/NodeInfo.py
/usr/lib64/python2.7/site-packages/xen/sv/NodeInfo.pyc
/usr/lib64/python2.7/site-packages/xen/sv/NodeInfo.pyo
/usr/lib64/python2.7/site-packages/xen/sv/RestoreDomain.py
/usr/lib64/python2.7/site-packages/xen/sv/RestoreDomain.pyc
/usr/lib64/python2.7/site-packages/xen/sv/RestoreDomain.pyo
/usr/lib64/python2.7/site-packages/xen/sv/Wizard.py
/usr/lib64/python2.7/site-packages/xen/sv/Wizard.pyc
/usr/lib64/python2.7/site-packages/xen/sv/Wizard.pyo
/usr/lib64/python2.7/site-packages/xen/sv/__init__.py
/usr/lib64/python2.7/site-packages/xen/sv/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/sv/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/sv/util.py
/usr/lib64/python2.7/site-packages/xen/sv/util.pyc
/usr/lib64/python2.7/site-packages/xen/sv/util.pyo
/usr/lib64/python2.7/site-packages/xen/web/SrvBase.py
/usr/lib64/python2.7/site-packages/xen/web/SrvBase.pyc
/usr/lib64/python2.7/site-packages/xen/web/SrvBase.pyo
/usr/lib64/python2.7/site-packages/xen/web/SrvDir.py
/usr/lib64/python2.7/site-packages/xen/web/SrvDir.pyc
/usr/lib64/python2.7/site-packages/xen/web/SrvDir.pyo
/usr/lib64/python2.7/site-packages/xen/web/__init__.py
/usr/lib64/python2.7/site-packages/xen/web/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/web/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/web/connection.py
/usr/lib64/python2.7/site-packages/xen/web/connection.pyc
/usr/lib64/python2.7/site-packages/xen/web/connection.pyo
/usr/lib64/python2.7/site-packages/xen/web/http.py
/usr/lib64/python2.7/site-packages/xen/web/http.pyc
/usr/lib64/python2.7/site-packages/xen/web/http.pyo
/usr/lib64/python2.7/site-packages/xen/web/httpserver.py
/usr/lib64/python2.7/site-packages/xen/web/httpserver.pyc
/usr/lib64/python2.7/site-packages/xen/web/httpserver.pyo
/usr/lib64/python2.7/site-packages/xen/web/protocol.py
/usr/lib64/python2.7/site-packages/xen/web/protocol.pyc
/usr/lib64/python2.7/site-packages/xen/web/protocol.pyo
/usr/lib64/python2.7/site-packages/xen/web/resource.py
/usr/lib64/python2.7/site-packages/xen/web/resource.pyc
/usr/lib64/python2.7/site-packages/xen/web/resource.pyo
/usr/lib64/python2.7/site-packages/xen/web/static.py
/usr/lib64/python2.7/site-packages/xen/web/static.pyc
/usr/lib64/python2.7/site-packages/xen/web/static.pyo
/usr/lib64/python2.7/site-packages/xen/web/tcp.py
/usr/lib64/python2.7/site-packages/xen/web/tcp.pyc
/usr/lib64/python2.7/site-packages/xen/web/tcp.pyo
/usr/lib64/python2.7/site-packages/xen/web/unix.py
/usr/lib64/python2.7/site-packages/xen/web/unix.pyc
/usr/lib64/python2.7/site-packages/xen/web/unix.pyo
/usr/lib64/python2.7/site-packages/xen/xend/Args.py
/usr/lib64/python2.7/site-packages/xen/xend/Args.pyc
/usr/lib64/python2.7/site-packages/xen/xend/Args.pyo
/usr/lib64/python2.7/site-packages/xen/xend/MemoryPool.py
/usr/lib64/python2.7/site-packages/xen/xend/MemoryPool.pyc
/usr/lib64/python2.7/site-packages/xen/xend/MemoryPool.pyo
/usr/lib64/python2.7/site-packages/xen/xend/PrettyPrint.py
/usr/lib64/python2.7/site-packages/xen/xend/PrettyPrint.pyc
/usr/lib64/python2.7/site-packages/xen/xend/PrettyPrint.pyo
/usr/lib64/python2.7/site-packages/xen/xend/Vifctl.py
/usr/lib64/python2.7/site-packages/xen/xend/Vifctl.pyc
/usr/lib64/python2.7/site-packages/xen/xend/Vifctl.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendAPI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendAPI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendAPI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIConstants.py
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIConstants.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIConstants.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIStore.py
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIStore.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIStore.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIVersion.py
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIVersion.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendAPIVersion.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendAuthSessions.py
/usr/lib64/python2.7/site-packages/xen/xend/XendAuthSessions.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendAuthSessions.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendBase.py
/usr/lib64/python2.7/site-packages/xen/xend/XendBase.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendBase.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendBootloader.py
/usr/lib64/python2.7/site-packages/xen/xend/XendBootloader.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendBootloader.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendCPUPool.py
/usr/lib64/python2.7/site-packages/xen/xend/XendCPUPool.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendCPUPool.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendCheckpoint.py
/usr/lib64/python2.7/site-packages/xen/xend/XendCheckpoint.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendCheckpoint.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendClient.py
/usr/lib64/python2.7/site-packages/xen/xend/XendClient.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendClient.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendConfig.py
/usr/lib64/python2.7/site-packages/xen/xend/XendConfig.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendConfig.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendConstants.py
/usr/lib64/python2.7/site-packages/xen/xend/XendConstants.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendConstants.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDPCI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDPCI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDPCI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDSCSI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDSCSI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDSCSI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDevices.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDevices.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDevices.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDmesg.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDmesg.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDmesg.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDomain.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDomain.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDomain.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendDomainInfo.py
/usr/lib64/python2.7/site-packages/xen/xend/XendDomainInfo.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendDomainInfo.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendError.py
/usr/lib64/python2.7/site-packages/xen/xend/XendError.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendError.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendLocalStorageRepo.py
/usr/lib64/python2.7/site-packages/xen/xend/XendLocalStorageRepo.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendLocalStorageRepo.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendLogging.py
/usr/lib64/python2.7/site-packages/xen/xend/XendLogging.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendLogging.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendMonitor.py
/usr/lib64/python2.7/site-packages/xen/xend/XendMonitor.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendMonitor.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendNetwork.py
/usr/lib64/python2.7/site-packages/xen/xend/XendNetwork.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendNetwork.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendNode.py
/usr/lib64/python2.7/site-packages/xen/xend/XendNode.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendNode.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendOptions.py
/usr/lib64/python2.7/site-packages/xen/xend/XendOptions.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendOptions.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendPBD.py
/usr/lib64/python2.7/site-packages/xen/xend/XendPBD.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendPBD.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendPIF.py
/usr/lib64/python2.7/site-packages/xen/xend/XendPIF.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendPIF.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendPIFMetrics.py
/usr/lib64/python2.7/site-packages/xen/xend/XendPIFMetrics.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendPIFMetrics.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendPPCI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendPPCI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendPPCI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendPSCSI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendPSCSI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendPSCSI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendProtocol.py
/usr/lib64/python2.7/site-packages/xen/xend/XendProtocol.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendProtocol.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendQCoWStorageRepo.py
/usr/lib64/python2.7/site-packages/xen/xend/XendQCoWStorageRepo.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendQCoWStorageRepo.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendSXPDev.py
/usr/lib64/python2.7/site-packages/xen/xend/XendSXPDev.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendSXPDev.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendStateStore.py
/usr/lib64/python2.7/site-packages/xen/xend/XendStateStore.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendStateStore.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendStorageRepository.py
/usr/lib64/python2.7/site-packages/xen/xend/XendStorageRepository.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendStorageRepository.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendTask.py
/usr/lib64/python2.7/site-packages/xen/xend/XendTask.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendTask.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendTaskManager.py
/usr/lib64/python2.7/site-packages/xen/xend/XendTaskManager.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendTaskManager.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendVDI.py
/usr/lib64/python2.7/site-packages/xen/xend/XendVDI.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendVDI.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendVMMetrics.py
/usr/lib64/python2.7/site-packages/xen/xend/XendVMMetrics.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendVMMetrics.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendVnet.py
/usr/lib64/python2.7/site-packages/xen/xend/XendVnet.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendVnet.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicy.py
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicy.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicy.pyo
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicyAdmin.py
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicyAdmin.pyc
/usr/lib64/python2.7/site-packages/xen/xend/XendXSPolicyAdmin.pyo
/usr/lib64/python2.7/site-packages/xen/xend/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/arch.py
/usr/lib64/python2.7/site-packages/xen/xend/arch.pyc
/usr/lib64/python2.7/site-packages/xen/xend/arch.pyo
/usr/lib64/python2.7/site-packages/xen/xend/balloon.py
/usr/lib64/python2.7/site-packages/xen/xend/balloon.pyc
/usr/lib64/python2.7/site-packages/xen/xend/balloon.pyo
/usr/lib64/python2.7/site-packages/xen/xend/encode.py
/usr/lib64/python2.7/site-packages/xen/xend/encode.pyc
/usr/lib64/python2.7/site-packages/xen/xend/encode.pyo
/usr/lib64/python2.7/site-packages/xen/xend/image.py
/usr/lib64/python2.7/site-packages/xen/xend/image.pyc
/usr/lib64/python2.7/site-packages/xen/xend/image.pyo
/usr/lib64/python2.7/site-packages/xen/xend/osdep.py
/usr/lib64/python2.7/site-packages/xen/xend/osdep.pyc
/usr/lib64/python2.7/site-packages/xen/xend/osdep.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/BlktapController.py
/usr/lib64/python2.7/site-packages/xen/xend/server/BlktapController.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/BlktapController.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/ConsoleController.py
/usr/lib64/python2.7/site-packages/xen/xend/server/ConsoleController.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/ConsoleController.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/DevConstants.py
/usr/lib64/python2.7/site-packages/xen/xend/server/DevConstants.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/DevConstants.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/DevController.py
/usr/lib64/python2.7/site-packages/xen/xend/server/DevController.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/DevController.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SSLXMLRPCServer.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SSLXMLRPCServer.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SSLXMLRPCServer.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDaemon.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDaemon.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDaemon.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDmesg.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDmesg.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDmesg.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomain.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomain.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomain.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomainDir.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomainDir.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvDomainDir.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvNode.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvNode.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvNode.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvRoot.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvRoot.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvRoot.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvServer.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvServer.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvServer.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvVnetDir.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvVnetDir.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvVnetDir.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvXendLog.py
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvXendLog.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/SrvXendLog.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/XMLRPCServer.py
/usr/lib64/python2.7/site-packages/xen/xend/server/XMLRPCServer.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/XMLRPCServer.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/server/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/blkif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/blkif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/blkif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/iopif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/iopif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/iopif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/irqif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/irqif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/irqif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/netif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/netif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/netif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/netif2.py
/usr/lib64/python2.7/site-packages/xen/xend/server/netif2.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/netif2.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/params.py
/usr/lib64/python2.7/site-packages/xen/xend/server/params.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/params.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/pciif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/pciif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/pciif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/pciquirk.py
/usr/lib64/python2.7/site-packages/xen/xend/server/pciquirk.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/pciquirk.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/relocate.py
/usr/lib64/python2.7/site-packages/xen/xend/server/relocate.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/relocate.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/test_controllers.py
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/test_controllers.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/tests/test_controllers.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/udevevent.py
/usr/lib64/python2.7/site-packages/xen/xend/server/udevevent.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/udevevent.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/vfbif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/vfbif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/vfbif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/vscsiif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/vscsiif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/vscsiif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/server/vusbif.py
/usr/lib64/python2.7/site-packages/xen/xend/server/vusbif.pyc
/usr/lib64/python2.7/site-packages/xen/xend/server/vusbif.pyo
/usr/lib64/python2.7/site-packages/xen/xend/sxp.py
/usr/lib64/python2.7/site-packages/xen/xend/sxp.pyc
/usr/lib64/python2.7/site-packages/xen/xend/sxp.pyo
/usr/lib64/python2.7/site-packages/xen/xend/tests/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/tests/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/tests/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_XendConfig.py
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_XendConfig.pyc
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_XendConfig.pyo
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_sxp.py
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_sxp.pyc
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_sxp.pyo
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_uuid.py
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_uuid.pyc
/usr/lib64/python2.7/site-packages/xen/xend/tests/test_uuid.pyo
/usr/lib64/python2.7/site-packages/xen/xend/uuid.py
/usr/lib64/python2.7/site-packages/xen/xend/uuid.pyc
/usr/lib64/python2.7/site-packages/xen/xend/uuid.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/__init__.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/stress_xs.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/stress_xs.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/tests/stress_xs.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xstransact.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xstransact.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xstransact.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xsutil.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xsutil.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xsutil.pyo
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xswatch.py
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xswatch.pyc
/usr/lib64/python2.7/site-packages/xen/xend/xenstore/xswatch.pyo
/usr/lib64/python2.7/site-packages/xen/xm/XenAPI.py
/usr/lib64/python2.7/site-packages/xen/xm/XenAPI.pyc
/usr/lib64/python2.7/site-packages/xen/xm/XenAPI.pyo
/usr/lib64/python2.7/site-packages/xen/xm/__init__.py
/usr/lib64/python2.7/site-packages/xen/xm/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xm/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xm/addlabel.py
/usr/lib64/python2.7/site-packages/xen/xm/addlabel.pyc
/usr/lib64/python2.7/site-packages/xen/xm/addlabel.pyo
/usr/lib64/python2.7/site-packages/xen/xm/console.py
/usr/lib64/python2.7/site-packages/xen/xm/console.pyc
/usr/lib64/python2.7/site-packages/xen/xm/console.pyo
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-create.py
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-create.pyc
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-create.pyo
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-new.py
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-new.pyc
/usr/lib64/python2.7/site-packages/xen/xm/cpupool-new.pyo
/usr/lib64/python2.7/site-packages/xen/xm/cpupool.py
/usr/lib64/python2.7/site-packages/xen/xm/cpupool.pyc
/usr/lib64/python2.7/site-packages/xen/xm/cpupool.pyo
/usr/lib64/python2.7/site-packages/xen/xm/create.py
/usr/lib64/python2.7/site-packages/xen/xm/create.pyc
/usr/lib64/python2.7/site-packages/xen/xm/create.pyo
/usr/lib64/python2.7/site-packages/xen/xm/dry-run.py
/usr/lib64/python2.7/site-packages/xen/xm/dry-run.pyc
/usr/lib64/python2.7/site-packages/xen/xm/dry-run.pyo
/usr/lib64/python2.7/site-packages/xen/xm/dumppolicy.py
/usr/lib64/python2.7/site-packages/xen/xm/dumppolicy.pyc
/usr/lib64/python2.7/site-packages/xen/xm/dumppolicy.pyo
/usr/lib64/python2.7/site-packages/xen/xm/getenforce.py
/usr/lib64/python2.7/site-packages/xen/xm/getenforce.pyc
/usr/lib64/python2.7/site-packages/xen/xm/getenforce.pyo
/usr/lib64/python2.7/site-packages/xen/xm/getlabel.py
/usr/lib64/python2.7/site-packages/xen/xm/getlabel.pyc
/usr/lib64/python2.7/site-packages/xen/xm/getlabel.pyo
/usr/lib64/python2.7/site-packages/xen/xm/getpolicy.py
/usr/lib64/python2.7/site-packages/xen/xm/getpolicy.pyc
/usr/lib64/python2.7/site-packages/xen/xm/getpolicy.pyo
/usr/lib64/python2.7/site-packages/xen/xm/help.py
/usr/lib64/python2.7/site-packages/xen/xm/help.pyc
/usr/lib64/python2.7/site-packages/xen/xm/help.pyo
/usr/lib64/python2.7/site-packages/xen/xm/labels.py
/usr/lib64/python2.7/site-packages/xen/xm/labels.pyc
/usr/lib64/python2.7/site-packages/xen/xm/labels.pyo
/usr/lib64/python2.7/site-packages/xen/xm/main.py
/usr/lib64/python2.7/site-packages/xen/xm/main.pyc
/usr/lib64/python2.7/site-packages/xen/xm/main.pyo
/usr/lib64/python2.7/site-packages/xen/xm/migrate.py
/usr/lib64/python2.7/site-packages/xen/xm/migrate.pyc
/usr/lib64/python2.7/site-packages/xen/xm/migrate.pyo
/usr/lib64/python2.7/site-packages/xen/xm/new.py
/usr/lib64/python2.7/site-packages/xen/xm/new.pyc
/usr/lib64/python2.7/site-packages/xen/xm/new.pyo
/usr/lib64/python2.7/site-packages/xen/xm/opts.py
/usr/lib64/python2.7/site-packages/xen/xm/opts.pyc
/usr/lib64/python2.7/site-packages/xen/xm/opts.pyo
/usr/lib64/python2.7/site-packages/xen/xm/resetpolicy.py
/usr/lib64/python2.7/site-packages/xen/xm/resetpolicy.pyc
/usr/lib64/python2.7/site-packages/xen/xm/resetpolicy.pyo
/usr/lib64/python2.7/site-packages/xen/xm/resources.py
/usr/lib64/python2.7/site-packages/xen/xm/resources.pyc
/usr/lib64/python2.7/site-packages/xen/xm/resources.pyo
/usr/lib64/python2.7/site-packages/xen/xm/rmlabel.py
/usr/lib64/python2.7/site-packages/xen/xm/rmlabel.pyc
/usr/lib64/python2.7/site-packages/xen/xm/rmlabel.pyo
/usr/lib64/python2.7/site-packages/xen/xm/setenforce.py
/usr/lib64/python2.7/site-packages/xen/xm/setenforce.pyc
/usr/lib64/python2.7/site-packages/xen/xm/setenforce.pyo
/usr/lib64/python2.7/site-packages/xen/xm/setpolicy.py
/usr/lib64/python2.7/site-packages/xen/xm/setpolicy.pyc
/usr/lib64/python2.7/site-packages/xen/xm/setpolicy.pyo
/usr/lib64/python2.7/site-packages/xen/xm/shutdown.py
/usr/lib64/python2.7/site-packages/xen/xm/shutdown.pyc
/usr/lib64/python2.7/site-packages/xen/xm/shutdown.pyo
/usr/lib64/python2.7/site-packages/xen/xm/tests/__init__.py
/usr/lib64/python2.7/site-packages/xen/xm/tests/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xm/tests/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xm/tests/test_create.py
/usr/lib64/python2.7/site-packages/xen/xm/tests/test_create.pyc
/usr/lib64/python2.7/site-packages/xen/xm/tests/test_create.pyo
/usr/lib64/python2.7/site-packages/xen/xm/xenapi_create.py
/usr/lib64/python2.7/site-packages/xen/xm/xenapi_create.pyc
/usr/lib64/python2.7/site-packages/xen/xm/xenapi_create.pyo
/usr/lib64/python2.7/site-packages/xen/xsview/__init__.py
/usr/lib64/python2.7/site-packages/xen/xsview/__init__.pyc
/usr/lib64/python2.7/site-packages/xen/xsview/__init__.pyo
/usr/lib64/python2.7/site-packages/xen/xsview/main.py
/usr/lib64/python2.7/site-packages/xen/xsview/main.pyc
/usr/lib64/python2.7/site-packages/xen/xsview/main.pyo
/usr/lib64/python2.7/site-packages/xen/xsview/xsviewer.py
/usr/lib64/python2.7/site-packages/xen/xsview/xsviewer.pyc
/usr/lib64/python2.7/site-packages/xen/xsview/xsviewer.pyo
/usr/lib64/xen/bin/libxl-save-helper
/usr/lib64/xen/bin/lsevtchn
/usr/lib64/xen/bin/pygrub
/usr/lib64/xen/bin/readnotes
/usr/lib64/xen/bin/xc_restore
/usr/lib64/xen/bin/xc_save
/usr/lib64/xen/bin/xenconsole
/usr/lib64/xen/bin/xenctx
/usr/lib64/xen/bin/xenpvnetboot
/usr/libexec/qemu-bridge-helper
/usr/sbin/blktapctrl
/usr/sbin/flask-get-bool
/usr/sbin/flask-getenforce
/usr/sbin/flask-label-pci
/usr/sbin/flask-loadpolicy
/usr/sbin/flask-set-bool
/usr/sbin/flask-setenforce
/usr/sbin/gdbsx
/usr/sbin/gtracestat
/usr/sbin/gtraceview
/usr/sbin/img2qcow
/usr/sbin/kdd
/usr/sbin/lock-util
/usr/sbin/qcow-create
/usr/sbin/qcow2raw
/usr/sbin/tap-ctl
/usr/sbin/tapdisk
/usr/sbin/tapdisk-client
/usr/sbin/tapdisk-diff
/usr/sbin/tapdisk-stream
/usr/sbin/tapdisk2
/usr/sbin/td-util
/usr/sbin/vhd-update
/usr/sbin/vhd-util
/usr/sbin/xen-bugtool
/usr/sbin/xen-hptool
/usr/sbin/xen-hvmcrash
/usr/sbin/xen-hvmctx
/usr/sbin/xen-lowmemd
/usr/sbin/xen-ringwatch
/usr/sbin/xen-tmem-list-parse
/usr/sbin/xenbaked
/usr/sbin/xenconsoled
/usr/sbin/xencov
/usr/sbin/xend
/usr/sbin/xenlockprof
/usr/sbin/xenmon.py
/usr/sbin/xenperf
/usr/sbin/xenpm
/usr/sbin/xenpmd
/usr/sbin/xentop
/usr/sbin/xentrace_setmask
/usr/sbin/xenwatchdogd
/usr/sbin/xl
/usr/sbin/xm
/usr/sbin/xsview
/usr/share/man/man1/xentop.1.gz
/usr/share/man/man1/xentrace_format.1.gz
/usr/share/man/man8/xentrace.8.gz
/usr/share/qemu-xen/qemu/bamboo.dtb
/usr/share/qemu-xen/qemu/bios.bin
/usr/share/qemu-xen/qemu/keymaps/ar
/usr/share/qemu-xen/qemu/keymaps/bepo
/usr/share/qemu-xen/qemu/keymaps/common
/usr/share/qemu-xen/qemu/keymaps/da
/usr/share/qemu-xen/qemu/keymaps/de
/usr/share/qemu-xen/qemu/keymaps/de-ch
/usr/share/qemu-xen/qemu/keymaps/en-gb
/usr/share/qemu-xen/qemu/keymaps/en-us
/usr/share/qemu-xen/qemu/keymaps/es
/usr/share/qemu-xen/qemu/keymaps/et
/usr/share/qemu-xen/qemu/keymaps/fi
/usr/share/qemu-xen/qemu/keymaps/fo
/usr/share/qemu-xen/qemu/keymaps/fr
/usr/share/qemu-xen/qemu/keymaps/fr-be
/usr/share/qemu-xen/qemu/keymaps/fr-ca
/usr/share/qemu-xen/qemu/keymaps/fr-ch
/usr/share/qemu-xen/qemu/keymaps/hr
/usr/share/qemu-xen/qemu/keymaps/hu
/usr/share/qemu-xen/qemu/keymaps/is
/usr/share/qemu-xen/qemu/keymaps/it
/usr/share/qemu-xen/qemu/keymaps/ja
/usr/share/qemu-xen/qemu/keymaps/lt
/usr/share/qemu-xen/qemu/keymaps/lv
/usr/share/qemu-xen/qemu/keymaps/mk
/usr/share/qemu-xen/qemu/keymaps/modifiers
/usr/share/qemu-xen/qemu/keymaps/nl
/usr/share/qemu-xen/qemu/keymaps/nl-be
/usr/share/qemu-xen/qemu/keymaps/no
/usr/share/qemu-xen/qemu/keymaps/pl
/usr/share/qemu-xen/qemu/keymaps/pt
/usr/share/qemu-xen/qemu/keymaps/pt-br
/usr/share/qemu-xen/qemu/keymaps/ru
/usr/share/qemu-xen/qemu/keymaps/sl
/usr/share/qemu-xen/qemu/keymaps/sv
/usr/share/qemu-xen/qemu/keymaps/th
/usr/share/qemu-xen/qemu/keymaps/tr
/usr/share/qemu-xen/qemu/kvmvapic.bin
/usr/share/qemu-xen/qemu/linuxboot.bin
/usr/share/qemu-xen/qemu/multiboot.bin
/usr/share/qemu-xen/qemu/openbios-ppc
/usr/share/qemu-xen/qemu/openbios-sparc32
/usr/share/qemu-xen/qemu/openbios-sparc64
/usr/share/qemu-xen/qemu/palcode-clipper
/usr/share/qemu-xen/qemu/petalogix-ml605.dtb
/usr/share/qemu-xen/qemu/petalogix-s3adsp1800.dtb
/usr/share/qemu-xen/qemu/ppc_rom.bin
/usr/share/qemu-xen/qemu/pxe-e1000.rom
/usr/share/qemu-xen/qemu/pxe-eepro100.rom
/usr/share/qemu-xen/qemu/pxe-ne2k_pci.rom
/usr/share/qemu-xen/qemu/pxe-pcnet.rom
/usr/share/qemu-xen/qemu/pxe-rtl8139.rom
/usr/share/qemu-xen/qemu/pxe-virtio.rom
/usr/share/qemu-xen/qemu/qemu-icon.bmp
/usr/share/qemu-xen/qemu/s390-zipl.rom
/usr/share/qemu-xen/qemu/sgabios.bin
/usr/share/qemu-xen/qemu/slof.bin
/usr/share/qemu-xen/qemu/spapr-rtas.bin
/usr/share/qemu-xen/qemu/vgabios-cirrus.bin
/usr/share/qemu-xen/qemu/vgabios-qxl.bin
/usr/share/qemu-xen/qemu/vgabios-stdvga.bin
/usr/share/qemu-xen/qemu/vgabios-vmware.bin
/usr/share/qemu-xen/qemu/vgabios.bin
/usr/share/xen/qemu/bamboo.dtb
/usr/share/xen/qemu/bios.bin
/usr/share/xen/qemu/keymaps/ar
/usr/share/xen/qemu/keymaps/common
/usr/share/xen/qemu/keymaps/da
/usr/share/xen/qemu/keymaps/de
/usr/share/xen/qemu/keymaps/de-ch
/usr/share/xen/qemu/keymaps/en-gb
/usr/share/xen/qemu/keymaps/en-us
/usr/share/xen/qemu/keymaps/es
/usr/share/xen/qemu/keymaps/et
/usr/share/xen/qemu/keymaps/fi
/usr/share/xen/qemu/keymaps/fo
/usr/share/xen/qemu/keymaps/fr
/usr/share/xen/qemu/keymaps/fr-be
/usr/share/xen/qemu/keymaps/fr-ca
/usr/share/xen/qemu/keymaps/fr-ch
/usr/share/xen/qemu/keymaps/hr
/usr/share/xen/qemu/keymaps/hu
/usr/share/xen/qemu/keymaps/is
/usr/share/xen/qemu/keymaps/it
/usr/share/xen/qemu/keymaps/ja
/usr/share/xen/qemu/keymaps/lt
/usr/share/xen/qemu/keymaps/lv
/usr/share/xen/qemu/keymaps/mk
/usr/share/xen/qemu/keymaps/modifiers
/usr/share/xen/qemu/keymaps/nl
/usr/share/xen/qemu/keymaps/nl-be
/usr/share/xen/qemu/keymaps/no
/usr/share/xen/qemu/keymaps/pl
/usr/share/xen/qemu/keymaps/pt
/usr/share/xen/qemu/keymaps/pt-br
/usr/share/xen/qemu/keymaps/ru
/usr/share/xen/qemu/keymaps/sl
/usr/share/xen/qemu/keymaps/sv
/usr/share/xen/qemu/keymaps/th
/usr/share/xen/qemu/keymaps/tr
/usr/share/xen/qemu/openbios-ppc
/usr/share/xen/qemu/openbios-sparc32
/usr/share/xen/qemu/openbios-sparc64
/usr/share/xen/qemu/ppc_rom.bin
/usr/share/xen/qemu/pxe-e1000.bin
/usr/share/xen/qemu/pxe-ne2k_pci.bin
/usr/share/xen/qemu/pxe-pcnet.bin
/usr/share/xen/qemu/pxe-rtl8139.bin
/usr/share/xen/qemu/vgabios-cirrus.bin
/usr/share/xen/qemu/vgabios.bin
/usr/share/xen/qemu/video.x

%changelog
* Thu Feb 21 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-9
- patch for [XSA-36, CVE-2013-0153] can cause boot time crash

* Fri Feb 15 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-8
- patch for [XSA-38, CVE-2013-0215] was flawed

* Fri Feb 08 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-7
- BuildRequires for texlive-kpathsea-bin wasn't needed
- correct gcc 4.8 fixes and follow suggestions upstream

* Tue Feb 05 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-6
- guest using oxenstored can crash host or exhaust memory [XSA-38,
  CVE-2013-0215] (#907888)
- guest using AMD-Vi for PCI passthrough can cause denial of service
  [XSA-36, CVE-2013-0153] (#910914)
- add some fixes for code which gcc 4.8 complains about
- additional BuildRequires are now needed for pod2text and pod2man
  also texlive-kpathsea-bin for mktexfmt

* Wed Jan 23 2013 Michael Young <m.a.young@durham.ac.uk>
- correct disabling of xendomains.service on uninstall

* Tue Jan 22 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-5
- nested virtualization on 32-bit guest can crash host [XSA-34,
  CVE-2013-0151] also nested HVM on guest can cause host to run out
  of memory [XSA-35, CVE-2013-0152] (#902792)
- restore status option to xend which is used by libvirt (#893699)

* Thu Jan 17 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-4
- Buffer overflow when processing large packets in qemu e1000 device
  driver [XSA-41, CVE-2012-6075] (#910845)

* Thu Jan 10 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-3
- fix some format errors in xl.cfg.pod.5 to allow build on F19

* Wed Jan 09 2013 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-2
- VT-d interrupt remapping source validation flaw [XSA-33,
    CVE-2012-5634] (#893568)
- pv guests can crash xen when xen built with debug=y (included for
    completeness - Fedora builds have debug=n) [XSA-37, CVE-2013-0154]

* Tue Dec 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.1-1
- update to xen-4.2.1
- remove patches that are included in 4.2.1
- rebase xen.fedora.efi.build.patch

* Thu Dec 13 2012 Richard W.M. Jones <rjones@redhat.com> - 4.2.0-7
- Rebuild for OCaml fix (RHBZ#877128).

* Mon Dec 03 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-6
- 6 security fixes
  A guest can cause xen to crash [XSA-26, CVE-2012-5510] (#883082)
  An HVM guest can cause xen to run slowly or crash [XSA-27, CVE-2012-5511]
    (#883084)
  A PV guest can cause xen to crash and might be able escalate privileges
    [XSA-29, CVE-2012-5513] (#883088)
  An HVM guest can cause xen to hang [XSA-30, CVE-2012-5514] (#883091)
  A guest can cause xen to hang [XSA-31, CVE-2012-5515] (#883092)
  A PV guest can cause xen to crash and might be able escalate privileges
    [XSA-32, CVE-2012-5525] (#883094)

* Sat Nov 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-5
- two build fixes for Fedora 19
- add texlive-ntgclass package to fix build

* Tue Nov 13 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-4
- 4 security fixes
  A guest can block a cpu by setting a bad VCPU deadline [XSA 20,
    CVE-2012-4535] (#876198)
  HVM guest can exhaust p2m table crashing xen [XSA 22, CVE-2012-4537] (#876203)
  PAE HVM guest can crash hypervisor [XSA-23, CVE-2012-4538] (#876205)
  32-bit PV guest on 64-bit hypervisor can cause an hypervisor infinite
    loop [XSA-24, CVE-2012-4539] (#876207)
- texlive-2012 is now in Fedora 18

* Sun Oct 28 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-3
- texlive-2012 isn't in Fedora 18 yet

* Fri Oct 26 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-2
- limit the size of guest kernels and ramdisks to avoid running out
  of memeory on dom0 during guest boot [XSA-25, CVE-2012-4544] (#870414)

* Thu Oct 25 2012 Michael Young <m.a.young@durham.ac.uk> - 4.2.0-1
- update to xen-4.2.0
- rebase xen-net-disable-iptables-on-bridge.patch pygrubfix.patch
- remove patches that are now upstream or with alternatives upstream
- use ipxe and seabios from seabios-bin and ipxe-roms-qemu packages
- xen tools now need ./configure to be run (x86_64 needs libdir set)
- don't build upstream qemu version
- amend list of files in package - relocate xenpaging
  add /etc/xen/xlexample* oxenstored.conf /usr/include/xenstore-compat/*
      xenstore-stubdom.gz xen-lowmemd xen-ringwatch xl.1.gz xl.cfg.5.gz
      xl.conf.5.gz xlcpupool.cfg.5.gz
- use a tmpfiles.d file to create /run/xen on boot
- add BuildRequires for yajl-devel and graphviz
- build an efi boot image where it is supported
- adjust texlive changes so spec file still works on Fedora 17

* Thu Oct 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-6
- add font packages to build requires due to 2012 version of texlive in F19
- use build requires of texlive-latex instead of tetex-latex which it
  obsoletes

* Wed Oct 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-5
- rebuild for ocaml update

* Thu Sep 06 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-4
- disable qemu monitor by default [XSA-19, CVE-2012-4411] (#855141)

* Wed Sep 05 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-3
- 5 security fixes
  a malicious 64-bit PV guest can crash the dom0 [XSA-12, CVE-2012-3494]
    (#854585)
  a malicious crash might be able to crash the dom0 or escalate privileges
    [XSA-13, CVE-2012-3495] (#854589)
  a malicious PV guest can crash the dom0 [XSA-14, CVE-2012-3496] (#854590)
  a malicious HVM guest can crash the dom0 and might be able to read
    hypervisor or guest memory [XSA-16, CVE-2012-3498] (#854593)
  an HVM guest could use VT100 escape sequences to escalate privileges to
    that of the qemu process [XSA-17, CVE-2012-3515] (#854599)

* Fri Aug 10 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.3-1 4.1.3-2
- update to 4.1.3
  includes fix for untrusted HVM guest can cause the dom0 to hang or
    crash [XSA-11, CVE-2012-3433] (#843582)
- remove patches that are now upstream
- remove some unnecessary compile fixes
- adjust upstream-23936:cdb34816a40a-rework for backported fix for
    upstream-23940:187d59e32a58
- replace pygrub.size.limits.patch with upstreamed version
- fix for (#845444) broke xend under systemd

* Tue Aug 07 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-25
- remove some unnecessary cache flushing that slow things down
- change python options on xend to reduce selinux problems (#845444)

* Thu Jul 26 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-24
- in rare circumstances an unprivileged user can crash an HVM guest
  [XSA-10,CVE-2012-3432] (#843766)

* Tue Jul 24 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-23
- add a patch to remove a dependency on PyXML and Require python-lxml
  instead of PyXML (#842843)

* Sun Jul 22 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-22
- adjust systemd service files not to report failures when running without
  a hypervisor or when xendomains.service doesn't find anything to start

* Sun Jul 22 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.1.2-21
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-20
- Apply three security patches
  64-bit PV guest privilege escalation vulnerability [CVE-2012-0217]
  guest denial of service on syscall/sysenter exception generation
    [CVE-2012-0218]
  PV guest host Denial of Service [CVE-2012-2934]

* Sat Jun 09 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-19
- adjust xend.service systemd file to avoid selinux problems

* Fri Jun 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-18
- Enable xenconsoled by default under systemd (#829732)

* Thu May 17 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-16 4.1.2-17
- make pygrub cope better with big files from guest (#818412 CVE-2012-2625)
- add patch from 4.1.3-rc2-pre to build on F17/8

* Sun Apr 15 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-15
- Make the udev tap rule more specific as it breaks openvpn (#812421)
- don't try setuid in xend if we don't need to so selinux is happier

* Sat Mar 31 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-14
- /var/lib/xenstored mount has wrong selinux permissions in latest Fedora
- load xen-acpi-processor module (kernel 3.4 onwards) if present

* Thu Mar 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-13
- fix a packaging error

* Thu Mar 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-12
- fix an error in an rpm script from the sysv configuration removal
- migrate xendomains script to systemd

* Wed Feb 29 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-11
- put the systemd files back in the right place

* Wed Feb 29 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-10
- clean up systemd and sysv configuration including removal of migrated
  sysv files for fc17+

* Sat Feb 18 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-9
- move xen-watchdog to systemd

* Wed Feb 08 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-8
- relocate systemd files for fc17+

* Tue Feb 07 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-7
- move xend and xenconsoled to systemd

* Thu Feb 02 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-6
- Fix buffer overflow in e1000 emulation for HVM guests [CVE-2012-0029]

* Sat Jan 28 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-5
- Start building xen's ocaml libraries if appropriate unless --without ocaml
  was specified
- add some backported patches from xen unstable (via Debian) for some
  ocaml tidying and fixes

* Sun Jan 15 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-4
- actually apply the xend-pci-loop.patch
- compile fixes for gcc-4.7

* Wed Jan 11 2012 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-3
- Add xend-pci-loop.patch to stop xend crashing with weird PCI cards (#767742)
- avoid a backtrace if xend can't log to the standard file or a 
  temporary directory (part of #741042)

* Mon Nov 21 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-2
- Fix lost interrupts on emulated devices
- stop xend crashing if its state files are empty at start up
- avoid a python backtrace if xend is run on bare metal
- update grub2 configuration after the old hypervisor has gone
- move blktapctrl to systemd
- Drop obsolete dom0-kernel.repo file

* Fri Oct 21 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.2-1
- update to 4.1.2
  remove upstream patches xen-4.1-testing.23104 and xen-4.1-testing.23112

* Fri Oct 14 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-8
- more pygrub improvements for grub2 on guest

* Thu Oct 13 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-7
- make pygrub work better with GPT partitions and grub2 on guest

* Thu Sep 29 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-5 4.1.1-6
- improve systemd functionality

* Wed Sep 28 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-4
- lsb header fixes - xenconsoled shutdown needs xenstored to be running
- partial migration to systemd to fix shutdown delays
- update grub2 configuration after hypervisor updates

* Sun Aug 14 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-3
- untrusted guest controlling PCI[E] device can lock up host CPU [CVE-2011-3131]

* Wed Jul 20 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-2
- clean up patch to solve a problem with hvmloader compiled with gcc 4.6

* Wed Jun 15 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.1-1
- update to 4.1.1
  includes various bugfixes and fix for [CVE-2011-1898] guest with pci
  passthrough can gain privileged access to base domain
- remove upstream cve-2011-1583-4.1.patch 

* Mon May 09 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-2
- Overflows in kernel decompression can allow root on xen PV guest to gain
  privileged access to base domain, or access to xen configuration info.
  Lack of error checking could allow DoS attack from guest [CVE-2011-1583]
- Don't require /usr/bin/qemu-nbd as it isn't used at present.

* Fri Mar 25 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-1
- update to 4.1.0 final

* Tue Mar 22 2011 Michael Young <m.a.young@durham.ac.uk> - 4.1.0-0.1.rc8
- update to 4.1.0-rc8 release candidate
- create xen-4.1.0-rc8.tar.xz file from git/hg repositories
- rebase xen-initscript.patch xen-dumpdir.patch
  xen-net-disable-iptables-on-bridge.patch localgcc45fix.patch
  sysconfig.xenstored init.xenstored
- remove unnecessary or conflicting xen-xenstore-cli.patch localpy27fixes.patch
  xen.irq.fixes.patch xen.xsave.disable.patch xen.8259afix.patch
  localcleanups.patch libpermfixes.patch
- add patch to allow pygrub to work with single partitions with boot sectors
- create ipxe-git-v1.0.0.tar.gz from http://git.ipxe.org/ipxe.git
  to avoid downloading at build time
- no need to move udev rules or init scripts as now created in the right place
- amend list of files shipped - remove fs-backend
  add init.d scripts xen-watchdog xencommons
  add config files xencommons xl.conf cpupool
  add programs kdd tap-ctl xen-hptool xen-hvmcrash xenwatchdogd

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0.1-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jan 31 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-9
- Make libraries executable so that rpm gets dependencies right

* Sat Jan 29 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-8
- Temporarily turn off some compile options so it will build on rawhide

* Fri Jan 28 2011 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-7
- ghost directories in /var/run (#656724)
- minor fixes to /usr/share/doc/xen-doc-4.?.?/misc/network_setup.txt (#653159)
  /etc/xen/scripts/network-route, /etc/xen/scripts/vif-common.sh (#669747)
  and /etc/sysconfig/modules/xen.modules (#656536)

* Tue Oct 12 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-6
- add upstream xen patch xen.8259afix.patch to fix boot panic
  "IO-APIC + timer doesn't work!" (#642108)

* Thu Oct 07 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-5
- add ext4 support for pvgrub (grub-ext4-support.patch from grub-0.97-66.fc14)

* Wed Sep 29 2010 jkeating - 4.0.1-4
- Rebuilt for gcc bug 634757

* Fri Sep 24 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-3
- create symlink for qemu-dm on x86_64 for compatibility with 3.4
- apply some patches destined for 4.0.2
    add some irq fixes
    disable xsave which causes problems for HVM

* Sun Aug 29 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-2
- fix compile problems on Fedora 15, I suspect due to gcc 4.5.1

* Wed Aug 25 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.1-1
- update to 4.0.1 release - many bug fixes
- xen-dev-create-cleanup.patch no longer needed
- remove part of localgcc45fix.patch no longer needed
- package new files /etc/bash_completion.d/xl.sh
  and /usr/sbin/gdbsx
- add patch to get xm and xend working with python 2.7

* Mon Aug 2 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-5
- add newer module names and xen-gntdev to xen.modules
- Update dom0-kernel.repo file to use repos.fedorapeople.org location

* Mon Jul 26 2010 Michael Young <m.a.young@durham.ac.uk>
- create a xen-licenses package to satisfy revised the Fedora
  Licensing Guidelines

* Sun Jul 25 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-4
- fix gcc 4.5 compile problems

* Thu Jul 22 2010 David Malcolm <dmalcolm@redhat.com> - 4.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Sun Jun 20 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-2
- add patch to remove some old device creation code that doesn't
  work with the latest pvops kernels

* Tue Jun 7 2010 Michael Young <m.a.young@durham.ac.uk> - 4.0.0-1
- update to 4.0.0 release
- rebase xen-initscript.patch and xen-dumpdir.patch patches
- adjust spec file for files added to or removed from the packages
- add new build dependencies libuuid-devel and iasl

* Tue Jun 1 2010 Michael Young <m.a.young@durham.ac.uk> - 3.4.3-1
- update to 3.4.3 release including
    support for latest pv_ops kernels (possibly incomplete)
    should fix build problems (#565063) and crashes (#545307)
- replace Prereq: with Requires: in spec file
- drop static libraries (#556101)

* Thu Dec 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.2-2
- adapt module load script to evtchn.ko -> xen-evtchn.ko rename.

* Thu Dec 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.2-1
- update to 3.4.2 release.
- drop backport patches.

* Fri Oct 8 2009 Justin M. Forbes <jforbes@redhat.com> - 3.4.1-5
- add PyXML to dependencies. (#496135)
- Take ownership of {_libdir}/fs (#521806)

* Mon Sep 14 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-4
- add e2fsprogs-devel to build dependencies.

* Tue Sep 2 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-3
- swap bzip2+xz linux kernel compression support patches.
- backport one more bugfix (videoram option).

* Tue Sep 1 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-2
- backport bzip2+xz linux kernel compression support.
- backport a few bugfixes.

* Fri Aug 7 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.1-1
- update to 3.4.1 release.

* Wed Aug 5 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-4
- Kill info files.  No xen docs, just standard gnu stuff.
- kill -Werror in tools/libxc to fix build.

* Mon Jul 27 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu May 28 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-2
- rename info files to fix conflict with binutils.
- add install-info calls for the doc subpackage.
- un-parallelize doc build.

* Wed May 27 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.4.0-1
- update to version 3.4.0.
- cleanup specfile, add doc subpackage.

* Tue Mar 10 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-11
- fix python 2.6 warnings.

* Fri Mar 6 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-9
- fix xen.modules init script for pv_ops kernel.
- stick rpm release tag into XEN_VENDORVERSION.
- use %{ix86} macro in ExclusiveArch.
- keep blktapctrl turned off by default.

* Mon Mar 2 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-7
- fix xenstored init script for pv_ops kernel.

* Fri Feb 27 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-6
- fix xenstored crash.
- backport qemu-unplug patch.

* Tue Feb 24 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-5
- fix gcc44 build (broken constrain in inline asm).
- fix ExclusiveArch

* Tue Feb 3 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-3
- backport bzImage support for dom0 builder.

* Sun Jan 18 2009 Tomas Mraz <tmraz@redhat.com> - 3.3.1-2
- rebuild with new openssl

* Thu Jan 8 2009 Gerd Hoffmann <kraxel@redhat.com> - 3.3.1-1
- update to xen 3.3.1 release.

* Wed Dec 17 2008 Gerd Hoffmann <kraxel@redhat.com> - 3.3.0-2
- build and package stub domains (pvgrub, ioemu).
- backport unstable fixes for pv_ops dom0.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 3.3.0-1.1
- Rebuild for Python 2.6

* Fri Aug 29 2008 Daniel P. Berrange <berrange@redhat.com> - 3.3.0-1.fc10
- Update to xen 3.3.0 release

* Wed Jul 23 2008 Mark McLoughlin <markmc@redhat.com> - 3.2.0-17.fc10
- Enable xen-hypervisor build
- Backport support for booting DomU from bzImage
- Re-diff all patches for zero fuzz

* Wed Jul  9 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-16.fc10
- Remove bogus ia64 hypercall arg (rhbz #433921)

* Fri Jun 27 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-15.fc10
- Re-enable QEMU image format auto-detection, without the security
  loopholes

* Wed Jun 25 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-14.fc10
- Rebuild for GNU TLS ABI change

* Fri Jun 13 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-13.fc10
- Correctly limit PVFB size (CVE-2008-1952)

* Tue Jun  3 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-12.fc10
- Move /var/run/xend into xen-runtime for pygrub (rhbz #442052)

* Wed May 14 2008 Markus Armbruster <armbru@redhat.com> - 3.2.0-11.fc10
- Disable QEMU image format auto-detection (CVE-2008-2004)
- Fix PVFB to validate frame buffer description (CVE-2008-1943)

* Wed Feb 27 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-10.fc9
- Fix block device checks for extendable disk formats

* Wed Feb 27 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-9.fc9
- Let XenD setup QEMU logfile (rhbz #435164)
- Fix PVFB use of event channel filehandle

* Sat Feb 23 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-8.fc9
- Fix block device extents check (rhbz #433560)

* Mon Feb 18 2008 Mark McLoughlin <markmc@redhat.com> - 3.2.0-7.fc9
- Restore some network-bridge patches lost during 3.2.0 rebase

* Wed Feb  6 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-6.fc9
- Fixed xenstore-ls to automatically use xenstored socket as needed

* Sun Feb  3 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-5.fc9
- Fix timer mode parameter handling for HVM
- Temporarily disable all Latex docs due to texlive problems (rhbz #431327)

* Fri Feb  1 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-4.fc9
- Add a xen-runtime subpackage to allow use of Xen without XenD
- Split init script out to one script per daemon
- Remove unused / broken / obsolete tools

* Mon Jan 21 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-3.fc9
- Remove legacy dependancy on python-virtinst

* Mon Jan 21 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-2.fc9
- Added XSM header files to -devel RPM

* Fri Jan 18 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-1.fc9
- Updated to 3.2.0 final release

* Thu Jan 10 2008 Daniel P. Berrange <berrange@redhat.com> - 3.2.0-0.fc9.rc5.dev16701.1
- Rebase to Xen 3.2 rc5 changeset 16701

* Thu Dec 13 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.2-3.fc9
- Re-factor to make it easier to test dev trees in RPMs
- Include hypervisor build if doing a dev RPM

* Fri Dec 07 2007 Release Engineering <rel-eng@fedoraproject.org> - 3.1.2-2.fc9
- Rebuild for deps

* Sat Dec  1 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.2-1.fc9
- Upgrade to 3.1.2 bugfix release

* Sat Nov  3 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-14.fc9
- Disable network-bridge script since it conflicts with NetworkManager
  which is now on by default

* Fri Oct 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-13.fc9
- Fixed xenbaked tmpfile flaw (CVE-2007-3919)

* Wed Oct 10 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-12.fc8
- Pull in QEMU BIOS boot menu patch from KVM package
- Fix QEMU patch for locating x509 certificates based on command line args
- Add XenD config options for TLS x509 certificate setup

* Wed Sep 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-11.fc8
- Fixed rtl8139 checksum calculation for Vista (rhbz #308201)

* Wed Sep 26 2007 Chris Lalancette <clalance@redhat.com> - 3.1.0-10.fc8
- QEmu NE2000 overflow check - CVE-2007-1321
- Pygrub guest escape - CVE-2007-4993

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-9.fc8
- Fix generation of manual pages (rhbz #250791)
- Really fix FC-6 32-on-64 guests

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-8.fc8
- Make 32-bit FC-6 guest PVFB work on x86_64 host

* Mon Sep 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-7.fc8
- Re-add support for back-compat FC6 PVFB support
- Fix handling of explicit port numbers (rhbz #279581)

* Wed Sep 19 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-6.fc8
- Don't clobber the VIF type attribute in FV guests (rhbz #296061)

* Tue Aug 28 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-5.fc8
- Added dep on openssl for blktap-qcow

* Tue Aug 28 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-4.fc8
- Switch PVFB over to use QEMU
- Backport QEMU VNC security patches for TLS/x509

* Wed Aug  1 2007 Markus Armbruster <armbru@redhat.com> - 3.1.0-3.fc8
- Put guest's native protocol ABI into xenstore, to provide for older
  kernels running 32-on-64.
- VNC keymap fixes
- Fix race conditions in LibVNCServer on client disconnect

* Tue Jun 12 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-2.fc8
- Remove patch which kills VNC monitor
- Fix HVM save/restore file path to be /var/lib/xen instead of /tmp
- Don't spawn a bogus xen-vncfb daemon for HVM guests
- Add persistent logging of hypervisor & guest consoles
- Add /etc/sysconfig/xen to allow admin choice of logging options
- Re-write Xen startup to use standard init script functions
- Add logrotate configuration for all xen related logs

* Fri May 25 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-1.fc8
- Updated to official 3.1.0 tar.gz
- Fixed data corruption from VNC client disconnect (bz 241303)

* Thu May 17 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-0.rc7.2.fc7
- Ensure xen-vncfb processes are cleanedup if guest quits (bz 240406)
- Tear down guest if device hotplug fails

* Thu May  3 2007 Daniel P. Berrange <berrange@redhat.com> - 3.1.0-0.rc7.1.fc7
- Updated to 3.1.0 rc7, changeset  15021 (upstream renumbered from 3.0.5)

* Tue May  1 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.4.fc7
- Fix op_save RPC API

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.3.fc7
- Added BR on gettext

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.2.fc7
- Redo failed build.

* Mon Apr 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc4.1.fc7
- Updated to 3.0.5 rc4, changeset 14993
- Reduce number of xenstore transactions used for listing domains
- Hack to pre-balloon 2 MB for PV guests as well as HVM

* Thu Apr 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc3.14934.2.fc7
- Fixed display of bootloader menu with xm create -c
- Added modprobe for both xenblktap & blktap to deal with rename issues
- Hack to pre-balloon 10 MB for HVM guests

* Thu Apr 26 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc3.14934.1.fc7
- Updated to 3.0.5 rc3, changeset 14934
- Fixed networking for service xend restart & minor IPv6 tweak

* Tue Apr 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc2.14889.2.fc7
- Fixed vfb/vkbd device startup race

* Tue Apr 24 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.5-0.rc2.14889.1.fc7
- Updated to xen 3.0.5 rc2, changeset 14889
- Remove use of netloop from network-bridge script
- Add backcompat support to vif-bridge script to translate xenbrN to ethN

* Wed Mar 14 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-9.fc7
- Disable access to QEMU monitor over VNC (CVE-2007-0998, bz 230295)

* Tue Mar  6 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-8.fc7
- Close QEMU file handles when running network script

* Fri Mar  2 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-7.fc7
- Fix interaction of bootloader with blktap (bz 230702)
- Ensure PVFB daemon terminates if domain doesn't startup (bz 230634)

* Thu Feb  8 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-6.fc7
- Setup readonly loop devices for readonly disks
- Extended error reporting for hotplug scripts
- Pass all 8 mouse buttons from VNC through to kernel

* Tue Jan 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-5.fc7
- Don't run the pvfb daemons for HVM guests (bz 225413)
- Fix handling of vnclisten parameter for HVM guests

* Tue Jan 30 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-4.fc7
- Fix pygrub memory corruption

* Tue Jan 23 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-3.fc7
- Added PVFB back compat for FC5/6 guests

* Mon Jan 22 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-2.fc7
- Ensure the arch-x86 header files are included in xen-devel package
- Bring back patch to move /var/xen/dump to /var/lib/xen/dump
- Make /var/log/xen mode 0700

* Thu Jan 11 2007 Daniel P. Berrange <berrange@redhat.com> - 3.0.4-1
- Upgrade to official xen-3.0.4_1 release tarball

* Thu Dec 14 2006 Jeremy Katz <katzj@redhat.com> - 3.0.3-3
- fix the build

* Thu Dec  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0.3-2
- rebuild for python 2.5

* Tue Oct 24 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.3-1
- Pull in the official 3.0.3 tarball of xen (changeset 11774).
- Add patches for VNC password authentication (bz 203196)
- Switch /etc/xen directory to be mode 0700 because the config files
  can contain plain text passwords (bz 203196)
- Change the package dependency to python-virtinst to reflect the
  package name change.
- Fix str-2-int cast of VNC port for paravirt framebuffer (bz 211193)

* Wed Oct  4 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-44
- fix having "many" kernels in pygrub

* Wed Oct  4 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-43
- Fix SMBIOS tables for SVM guests [danpb] (bug 207501)

* Fri Sep 29 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.2-42
- Added vnclisten patches to make VNC only listen on localhost
  out of the box, configurable by 'vnclisten' parameter (bz 203196)

* Thu Sep 28 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-41
- Update to xen-3.0.3-testing changeset 11633

* Thu Sep 28 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-40
- Workaround blktap/xenstore startup race
- Add udev rules for xen blktap devices (srostedt)
- Add support for dynamic blktap device nodes (srostedt)
- Fixes for infinite dom0 cpu usage with blktap
- Fix xm not to die on malformed "tap:" blkif config string
- Enable blktap on kernels without epoll-for-aio support.
- Load the blktap module automatically at startup
- Reenable blktapctrl

* Wed Sep 27 2006 Daniel Berrange <berrange@redhat.com> - 3.0.2-39
- Disable paravirt framebuffer server side rendered cursor (bz 206313)
- Ignore SIGPIPE in paravirt framebuffer daemon to avoid terminating
  on client disconnects while writing data (bz 208025)

* Wed Sep 27 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-38
- Fix cursor in pygrub (#208041)

* Tue Sep 26 2006 Daniel P. Berrange <berrange@redhat.com> - 3.0.2-37
- Removed obsolete scary warnings in package description

* Thu Sep 21 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-36
- Add Requires: kpartx for dom0 access to domU data

* Wed Sep 20 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-35
- Don't strip qemu-dm early, so that we get proper debuginfo (danpb)
- Fix compile problem with latest glibc

* Wed Sep 20 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-34
- Update to xen-unstable changeset 11539
- Threading fixes for libVNCserver (danpb)

* Tue Sep  5 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-33
- update pvfb patch based on upstream feedback

* Tue Sep  5 2006 Juan Quintela <quintela@redhat.com> - 3.0.2-31
- re-enable ia64.

* Thu Aug 31 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-31
- update to changeset 11405

* Thu Aug 31 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-30
- fix pvfb for x86_64

* Wed Aug 30 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-29
- update libvncserver to hopefully fix problems with vnc clients disconnecting

* Tue Aug 29 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-28
- fix a typo

* Mon Aug 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-27
- add support for paravirt framebuffer

* Mon Aug 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-26
- update to xen-unstable cs 11251
- clean up patches some
- disable ia64 as it doesn't currently build 

* Tue Aug 22 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-25
- make initscript not spew on non-xen kernels (#202945)

* Mon Aug 21 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-24
- remove copy of xenguest-install from this package, require 
  python-xeninst (the new home of xenguest-install)

* Wed Aug  2 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-23
- add patch to fix rtl8139 in FV, switch it back to the default nic
- add necessary ia64 patches (#201040)
- build on ia64

* Fri Jul 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-22
- add patch to fix net devices for HVM guests 

* Fri Jul 28 2006 Rik van Riel <riel@redhat.com> - 3.0.2-21
- make sure disk IO from HVM guests actually hits disk (#198851)

* Fri Jul 28 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-20
- don't start blktapctrl for now
- fix HVM guest creation in xenguest-install
- make sure log files have the right SELinux label

* Tue Jul 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-19
- fix libblktap symlinks (#199820)
- make libxenstore executable (#197316)
- version libxenstore (markmc) 

* Fri Jul 21 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-18
- include /var/xen/dump in file list
- load blkbk, netbk and netloop when xend starts
- update to cs 10712
- avoid file conflicts with qemu (#199759)

* Wed Jul 19 2006 Mark McLoughlin <markmc@redhat.com> - 3.0.2-17
- libxenstore is unversioned, so make xen-libs own it rather
  than xen-devel

* Wed Jul 19 2006 Mark McLoughlin <markmc@redhat.com> 3.0.2-16
- Fix network-bridge error (#199414)

* Mon Jul 17 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-15
- desactivating the relocation server in xend conf by default and
  add a warning text about it.

* Thu Jul 13 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-14
- Compile fix: don't #include <linux/compiler.h>

* Thu Jul 13 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-13
- Update to xen-unstable cset 10675
- Remove internal libvncserver build, new qemu device model has its own one
  now.
- Change default FV NIC model from rtl8139 to ne2k_pci until the former works
  better

* Tue Jul 11 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-12
- bump libvirt requires to 0.1.2
- drop xend httpd localhost server and use the unix socket instead

* Mon Jul 10 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-11
- split into main packages + -libs and -devel subpackages for #198260
- add patch from jfautley to allow specifying other bridge for 
  xenguest-install (#198097)

* Mon Jul  3 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-10
- make xenguest-install work with relative paths to disk 
  images (markmc, #197518)

* Fri Jun 23 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-9
- own /var/run/xend for selinux (#196456, #195952)

* Tue Jun 13 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-8
- fix syntax error in xenguest-install

* Mon Jun 12 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-7
- more initscript patch to report status #184452

* Wed Jun  7 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-6
- Add BuildRequires: for gnu/stubs-32.h so that x86_64 builds pick up
  glibc32 correctly

* Wed Jun  7 2006 Stephen C. Tweedie <sct@redhat.com> - 3.0.2-5
- Rebase to xen-unstable cset 10278

* Fri May  5 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-4
- update to new snapshot (changeset 9925)

* Thu Apr 27 2006 Daniel Veillard <veillard@redhat.com> - 3.0.2-3
- xen.h now requires xen-compat.h, install it too

* Wed Apr 26 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-2
- -m64 patch isn't needed anymore either

* Tue Apr 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0.2-1
- update to post 3.0.2 snapshot (changeset:   9744:1ad06bd6832d)
- stop applying patches that are upstreamed
- add patches for bootloader to run on all domain creations
- make xenguest-install create a persistent uuid
- use libvirt for domain creation in xenguest-install, slightly improve 
  error handling

* Tue Apr 18 2006 Daniel Veillard <veillard@redhat.com> - 3.0.1-5
- augment the close on exec patch with the fix for #188361

* Thu Mar  9 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-4
- add udev rule so that /dev/xen/evtchn gets created properly
- make pygrub not use /tmp for SELinux
- make xenguest-install actually unmount its nfs share.  also, don't use /tmp

* Tue Mar  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-3
- set /proc/xen/privcmd and /var/log/xend-debug.log as close on exec to avoid
  SELinux problems
- give better feedback on invalid urls (#184176)

* Mon Mar  6 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-2
- Use kva mmap to find the xenstore page (upstream xen-unstable cset 9130)

* Mon Mar  6 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-1
- fix xenguest-install so that it uses phy: for block devices instead of 
  forcing them over loopback.  
- change package versioning to be a little more accurate

* Thu Mar  2 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060301.fc5.3
- Remove unneeded CFLAGS spec file hack

* Thu Mar  2 2006 Rik van Riel <riel@redhat.com> - 3.0.1-0.20060301.fc5.2
- fix 64 bit CFLAGS issue with vmxloader and hvmloader

* Wed Mar  1 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060301.fc5.1
- Update to xen-unstable cset 9022

* Tue Feb 28 2006 Stephen Tweedie <sct@redhat.com> - 3.0.1-0.20060228.fc5.1
- Update to xen-unstable cset 9015

* Thu Feb 23 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.3
- add patch to ensure we get a unique fifo for boot loader (#182328)
- don't try to read the whole disk if we can't find a partition table 
  with pygrub 
- fix restarting of domains (#179677)

* Thu Feb  9 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.2
- fix -h conflict for xenguest-isntall

* Wed Feb  8 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5.1
- turn on http listener so you can do things with libvir as a user

* Wed Feb  8 2006 Jeremy Katz <katzj@redhat.com> - 3.0.1-0.20060208.fc5
- update to current hg snapshot for HVM support
- update xenguest-install for hvm changes.  allow hvm on svm hardware
- fix a few little xenguest-install bugs

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.6
- add a hack to fix VMX guests with video to balloon enough (#180375)

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.5
- fix build for new udev

* Tue Feb  7 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060130.fc5.4
- patch from David Lutterkort to pass macaddr (-m) to xenguest-install
- rework xenguest-install a bit so that it can be used for creating 
  fully-virtualized guests as well as paravirt.  Run with --help for 
  more details (or follow the prompts)
- add more docs (noticed by Andrew Puch)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 3.0-0.20060130.fc5.3.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Thu Feb  2 2006 Bill Nottingham <notting@redhat.com> 3.0-0.20060130.fc5.3
- disable iptables/ip6tables/arptables on bridging when bringing up a
  Xen bridge. If complicated filtering is needed that uses this, custom
  firewalls will be needed. (#177794)

* Tue Jan 31 2006 Bill Nottingham <notting@redhat.com> 3.0-0.20060130.fc5.2
- use the default network device, don't hardcode eth0

* Tue Jan 31 2006  <sct@redhat.com> - 3.0-0.20060130.fc5.1
- Add xenguest-install.py in /usr/sbin

* Mon Jan 30 2006  <sct@redhat.com> - 3.0-0.20060130.fc5
- Update to xen-unstable from 20060130 (cset 8705)

* Wed Jan 25 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060110.fc5.5
- buildrequire dev86 so that vmx firmware gets built
- include a copy of libvncserver and build vmx device models against it 

* Tue Jan 24 2006 Bill Nottingham <notting@redhat.com> - 3.0-0.20060110.fc5.4
- only put the udev rules in one place

* Fri Jan 20 2006 Jeremy Katz <katzj@redhat.com> - 3.0-0.20060110.fc5.3
- move xsls to xenstore-ls to not conflict (#171863)

* Tue Jan 10 2006  <sct@redhat.com> - 3.0-0.20060110.fc5.1
- Update to xen-unstable from 20060110 (cset 8526)

* Thu Dec 22 2005 Jesse Keating <jkeating@redhat.com> - 3.0-0.20051206.fc5.2
- rebuilt

* Tue Dec  6 2005 Juan Quintela <quintela@trasno.org> - 3.0-0.20051206.fc5.1
- 20051206 version (should be 3.0.0).
- Remove xen-bootloader fixes (integrated upstream).

* Wed Nov 30 2005 Daniel Veillard <veillard@redhat.com> - 3.0-0.20051109.fc5.4
- adding missing headers for libxenctrl and libxenstore
- use libX11-devel build require instead of xorg-x11-devel

* Mon Nov 14 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.3
- change default dom0 min-mem to 256M so that dom0 will try to balloon down

* Sat Nov 12 2005 Jeremy Katz <katzj@redhat.com>
- buildrequire ncurses-devel (reported by Justin Dearing)

* Thu Nov 10 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.2
- actually enable the initscripts

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5.1
- udev rules moved

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051109.fc5
- update to current -unstable
- add patches to fix pygrub 

* Wed Nov  9 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051108.fc5
- update to current -unstable

* Fri Oct 21 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20051021.fc5
- update to current -unstable

* Thu Sep 15 2005 Jeremy Katz <katzj@redhat.com> - 3.0-0.20050912.fc5.1
- doesn't require twisted anymore

* Mon Sep 12 2005 Rik van Riel <riel@redhat.com> 3.0-0.20050912.fc5
- add /var/{lib,run}/xenstored to the %files section (#167496, #167121)
- upgrade to today's Xen snapshot
- some small build fixes for x86_64
- enable x86_64 builds

* Thu Sep  8 2005 Rik van Riel <riel@redhat.com> 3.0-0.20050908
- explicitly call /usr/sbin/xend from initscript (#167407)
- add xenstored directories to spec file (#167496, #167121)
- misc gcc4 fixes 
- spec file cleanups (#161191)
- upgrade to today's Xen snapshot
- change the version to 3.0-0.<date> (real 3.0 release will be 3.0-1)

* Mon Aug 23 2005 Rik van Riel <riel@redhat.com> 2-20050823
- upgrade to today's Xen snapshot

* Mon Aug 15 2005 Rik van Riel <riel@redhat.com> 2-20050726
- upgrade to a known-working newer Xen, now that execshield works again

* Mon May 30 2005 Rik van Riel <riel@redhat.com> 2-20050530
- create /var/lib/xen/xen-db/migrate directory so "xm save" works (#158895)

* Mon May 23 2005 Rik van Riel <riel@redhat.com> 2-20050522
- change default display method for VMX domains to SDL

* Fri May 20 2005 Rik van Riel <riel@redhat.com> 2-20050520
- qemu device model for VMX

* Thu May 19 2005 Rik van Riel <riel@redhat.com> 2-20050519
- apply some VMX related bugfixes

* Mon Apr 25 2005 Rik van Riel <riel@redhat.com> 2-20050424
- upgrade to last night's snapshot

* Fri Apr 15 2005 Jeremy Katz <katzj@redhat.com>
- patch manpath instead of moving in specfile.  patch sent upstream
- install to native python path instead of /usr/lib/python
- other misc specfile duplication cleanup

* Sun Apr  3 2005 Rik van Riel <riel@redhat.com> 2-20050403
- fix context switch between vcpus in same domain, vcpus > cpus works again

* Sat Apr  2 2005 Rik van Riel <riel@redhat.com> 2-20050402
- move initscripts to /etc/rc.d/init.d (Florian La Roche) (#153188)
- ship only PDF documentation, not the PS or tex duplicates

* Thu Mar 31 2005 Rik van Riel <riel@redhat.com> 2-20050331
- upgrade to new xen hypervisor
- minor gcc4 compile fix

* Mon Mar 28 2005 Rik van Riel <riel@redhat.com> 2-20050328
- do not yet upgrade to new hypervisor ;)
- add barrier to fix SMP boot bug
- add tags target
- add zlib-devel build requires (#150952)

* Wed Mar  9 2005 Rik van Riel <riel@redhat.com> 2-20050308
- upgrade to last night's snapshot
- new compile fix patch

* Sun Mar  6 2005 Rik van Riel <riel@redhat.com> 2-20050305
- the gcc4 compile patches are now upstream
- upgrade to last night's snapshot, drop patches locally

* Fri Mar  4 2005 Rik van Riel <riel@redhat.com> 2-20050303
- finally got everything to compile with gcc4 -Wall -Werror

* Thu Mar  3 2005 Rik van Riel <riel@redhat.com> 2-20050303
- upgrade to last night's Xen-unstable snapshot
- drop printf warnings patch, which is upstream now

* Wed Feb 23 2005 Rik van Riel <riel@redhat.com> 2-20050222
- upgraded to last night's Xen snapshot
- compile warning fixes are now upstream, drop patch

* Sat Feb 19 2005 Rik van Riel <riel@redhat.com> 2-20050219
- fix more compile warnings
- fix the fwrite return check

* Fri Feb 18 2005 Rik van Riel <riel@redhat.com> 2-20050218
- upgrade to last night's Xen snapshot
- a kernel upgrade is needed to run this Xen, the hypervisor
  interface changed slightly
- comment out unused debugging function in plan9 domain builder
  that was giving compile errors with -Werror

* Tue Feb  8 2005 Rik van Riel <riel@redhat.com> 2-20050207
- upgrade to last night's Xen snapshot

* Tue Feb  1 2005 Rik van Riel <riel@redhat.com> 2-20050201.1
- move everything to /var/lib/xen

* Tue Feb  1 2005 Rik van Riel <riel@redhat.com> 2-20050201
- upgrade to new upstream Xen snapshot

* Tue Jan 25 2005 Jeremy Katz <katzj@redhat.com>
- add buildreqs on python-devel and xorg-x11-devel (strange AT nsk.no-ip.org)

* Mon Jan 24 2005 Rik van Riel <riel@redhat.com> - 2-20050124
- fix /etc/xen/scripts/network to not break with ipv6 (also sent upstream)

* Fri Jan 14 2005 Jeremy Katz <katzj@redhat.com> - 2-20050114
- update to new snap
- python-twisted is its own package now
- files are in /usr/lib/python now as well, ugh.

* Tue Jan 11 2005 Rik van Riel <riel@redhat.com>
- add segment fixup patch from xen tree
- fix %files list for python-twisted

* Mon Jan 10 2005 Rik van Riel <riel@redhat.com>
- grab newer snapshot, that does start up
- add /var/xen/xend-db/{domain,vnet} to %files section

* Thu Jan  6 2005 Rik van Riel <riel@redhat.com>
- upgrade to new snapshot of xen-unstable

* Mon Dec 13 2004 Rik van Riel <riel@redhat.com>
- build python-twisted as a subpackage
- update to latest upstream Xen snapshot

* Sun Dec  5 2004 Rik van Riel <riel@redhat.com>
- grab new Xen tarball (with wednesday's patch already included)
- transfig is a buildrequire, add it to the spec file

* Wed Dec  1 2004 Rik van Riel <riel@redhat.com>
- fix up Che's spec file a little bit
- create patch to build just Xen, not the kernels

* Wed Dec 01 2004 Che
- initial rpm release
