%define name	dkms-nouveau
%define oname	drm
%define mname	nouveau

%define version	0.0.13
%define snapshot 20090530
%define release %mkrel 0.%{snapshot}.1

Summary:	Nouveau DRI kernel DKMS module
Name:		%{name}
Version:	%{version}
Release:	%{release}
License:	MIT and GPLv2+
Group:		System/Kernel and hardware
# git clone git://anongit.freedesktop.org/git/mesa/drm/ ; cd drm
# git archive --prefix=drm-$(date +%Y%m%d)/ --format=tar HEAD | bzip2 > ../drm-$(date +%Y%m%d).tar.bz2
Source0:	%{oname}-%{snapshot}.tar.bz2
Obsoletes:	dkms-drm-experimental < 2.3.6
Requires:	dkms
Requires(post):	dkms
Requires(preun):dkms
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-buildroot

%description
Open source DRI/DRM kernel module for NVIDIA cards using DKMS.

%prep
%setup -q -n %{oname}-%{snapshot}
cd linux-core
sh ../scripts/create_linux_pci_lists.sh < ../shared-core/drm_pciids.txt
# Now we hack the drm to coexist with kernel drm (can't still be loaded
# at the same time due to /sys conflicts etc).
# Rename exported symbols drm* => drm_mdv_nouveau*
sed -r -i $(for i in $(sed -nr '/EXPORT_SYMBOL/s,^.*EXPORT_SYMBOL.*\((.+)\);.*$,\1,p' drm*.[ch] | grep ^drm); do echo -n "-e s,$i([^a-z_-]),drm_mdv_nouveau_${i#drm}\1,g "; done) *.[ch]
mv -f Makefile.kernel Makefile
# Rename module
sed -i -e 's,drm\.o,drm-mdv-nouveau\.o,' -e 's,drm-objs,drm-mdv-nouveau-objs,' Makefile
# Enable nouveau and disable others:
sed -i -e 's,$(CONFIG_DRM_NOUVEAU),m,' Makefile
sed -i -r -e 's,\$\(CONFIG_DRM_[A-Z0-9_]+\),n,' Makefile

# confirm version
[ %version = $(awk -v ORS= '/define DRIVER_MAJOR/{ print $3"." } /define DRIVER_MINOR/{ print $3"." } /define DRIVER_PATCHLEVEL/{ print $3 }' nouveau_drv.h) ]

rm -rv linux

%install
rm -rf %{buildroot}
install -d -m755 %{buildroot}%{_usrsrc}/%{mname}-%{version}-%{release}
install -m644 linux-core/* %{buildroot}%{_usrsrc}/%{mname}-%{version}-%{release}
ln -s . %{buildroot}%{_usrsrc}/%{mname}-%{version}-%{release}/linux
cat > %{buildroot}%{_usrsrc}/%{mname}-%{version}-%{release}/dkms.conf <<EOF
PACKAGE_NAME="%{mname}"
PACKAGE_VERSION="%{version}-%{release}"
MAKE[0]="make -C \${kernel_source_dir} M=\\\$(pwd)"
CLEAN="make -C \${kernel_source_dir} M=\\\$(pwd) clean"
AUTOINSTALL=YES
BUILT_MODULE_NAME[0]=nouveau
DEST_MODULE_LOCATION[0]="/kernel/nouveau"
BUILT_MODULE_NAME[1]=drm-mdv-nouveau
DEST_MODULE_LOCATION[1]="/kernel/nouveau"
EOF

%clean
rm -rf %{buildroot}

%post
dkms add     -m %{mname} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms build   -m %{mname} -v %{version}-%{release} --rpm_safe_upgrade &&
dkms install -m %{mname} -v %{version}-%{release} --rpm_safe_upgrade --force &&
rmmod nouveau drm drm_mdv_nouveau nvidia &>/dev/null
true

%preun
dkms remove  -m %{mname} -v %{version}-%{release} --rpm_safe_upgrade --all
true

%files
%defattr(-,root,root)
%{_usrsrc}/%{mname}-%{version}-%{release}
