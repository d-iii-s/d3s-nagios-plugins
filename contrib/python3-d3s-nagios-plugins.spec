Name:           python3-d3s-nagios-plugins
Version:        1.0.4
Release:        1%{?dist}
Summary:        A collection of various mini-plugins for Nagios

License:        APACHE-2
URL:            https://github.com/d-iii-s/d3s-nagios-plugins
Source0:        https://files.pythonhosted.org/packages/source/d/d3s-nagios-plugins/d3s_nagios_plugins-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

# Use pyproject.toml on modern systems
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
BuildRequires:  python3-wheel
BuildRequires:  pyproject-rpm-macros
%endif


%description
Contains plugins check_health, check_memory, check_os_updates and check_systemd_service.

%prep
%autosetup -n d3s_nagios_plugins-%{version}

%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%generate_buildrequires
%pyproject_buildrequires
%endif

%build
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%pyproject_wheel
%else
%{__python3} setup.py build
%endif

%install
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%pyproject_install
%else
%{__python3} setup.py install --skip-build --root=%{buildroot} --prefix=%{_prefix}
%endif

# Move scripts to Nagios plugins directory
install -d %{buildroot}%{_libdir}/nagios/plugins
mv %{buildroot}%{_bindir}/nagios_d3s_check_health %{buildroot}%{_libdir}/nagios/plugins/check_health
mv %{buildroot}%{_bindir}/nagios_d3s_check_memory %{buildroot}%{_libdir}/nagios/plugins/check_memory
mv %{buildroot}%{_bindir}/nagios_d3s_check_os_updates %{buildroot}%{_libdir}/nagios/plugins/check_os_updates
mv %{buildroot}%{_bindir}/nagios_d3s_check_systemd_service %{buildroot}%{_libdir}/nagios/plugins/check_systemd_service

%files
%{python3_sitelib}/
%license LICENSE
%doc README.md
%{_libdir}/nagios/plugins/

%changelog
