Name:           python3-d3s-nagios-plugins
Version:        1.0.3
Release:        1%{?dist}
Summary:        A collection of various mini-plugins for Nagios

License:        APACHE-2
URL:            https://github.com/d-iii-s/d3s-nagios-plugins
Source0:        https://files.pythonhosted.org/packages/ee/1d/bf0011a62f9721c88213efbd9b30d4a66239f517faf30ab277959beac4a6/d3s_nagios_plugins-1.0.3.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-wheel
BuildRequires:  python3-setuptools_scm
BuildRequires:  pyproject-rpm-macros

%description
Contains plugins check_health, check_memory, check_os_updates and check_systemd_service.

%prep
%autosetup -n d3s_nagios_plugins-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files d3s
install -d %{buildroot}%{_libdir}/nagios/plugins
mv %{buildroot}%{_bindir}/nagios_d3s_check_health %{buildroot}%{_libdir}/nagios/plugins/check_health
mv %{buildroot}%{_bindir}/nagios_d3s_check_memory %{buildroot}%{_libdir}/nagios/plugins/check_memory
mv %{buildroot}%{_bindir}/nagios_d3s_check_os_updates %{buildroot}%{_libdir}/nagios/plugins/check_os_updates
mv %{buildroot}%{_bindir}/nagios_d3s_check_systemd_service %{buildroot}%{_libdir}/nagios/plugins/check_systemd_service

%files -n python3-d3s-nagios-plugins -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_libdir}/nagios/plugins/

%changelog
