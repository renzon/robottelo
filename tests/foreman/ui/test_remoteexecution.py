"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from datetime import datetime, timedelta
from nailgun import entities
from robottelo.constants import (
    DEFAULT_LOC_ID,
    DISTRO_RHEL7,
    OS_TEMPLATE_DATA_FILE,
)
from robottelo.config import settings
from robottelo.datafactory import (
    gen_string,
    generate_strings_list,
    invalid_values_list,
)
from robottelo.cli.job_invocation import JobInvocation
from robottelo.decorators import (
    skip_if_not_set,
    stubbed,
    tier1,
    tier2,
    tier3,
    upgrade,
)
from robottelo.helpers import add_remote_execution_ssh_key, get_data_file
from robottelo.cli.host import Host
from robottelo.test import UITestCase
from robottelo.ui.factory import make_job_template, set_context
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session
from robottelo.vm import VirtualMachine

OS_TEMPLATE_DATA_FILE = get_data_file(OS_TEMPLATE_DATA_FILE)


class JobsTemplateTestCase(UITestCase):
    """Test class for jobs template feature"""

    @classmethod
    def setUpClass(cls):
        """Create an organization and host which can be re-used in tests."""
        super(JobsTemplateTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.host = entities.Host(organization=cls.organization).create()
        entities.OperatingSystem(
            id=cls.host.operatingsystem.id, family='Redhat').update(['family'])

    @tier1
    def test_positive_create_simple_job_template(self):
        """Create a simple Job Template

        :id: 7cb1e5b0-5420-47c5-bb43-e2c58bed7a9d

        :Steps:

            1. Navigate to Hosts -> Job Templates
            2. Enter a valid name
            3. Populate the template code
            4. Navigate to the job tab
            5. Enter a job name
            6. Click submit

        :expectedresults: The job template was successfully created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='input',
                        template_content=gen_string('alphanumeric', 500),
                    )
                    self.assertIsNotNone(self.jobtemplate.search(name))

    @tier1
    def test_positive_template_upload(self):
        """Use a template file to populate the job template

        :id: 976cf310-b2af-41bd-845a-f08baa2e8490

        :Setup: Create or use a pre-made job template file

        :Steps:

            1. Create a new job template.
            2. Enter a valid name
            3. Click the upload button to upload a template from the file
            4. Select the file with the desired template

        :expectedresults: Verify the template correctly imported the file's
            contents

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='file',
                        template_content=OS_TEMPLATE_DATA_FILE,
                    )
                    self.assertIsNotNone(self.jobtemplate.search(name))

    @tier1
    def test_positive_create_job_template_input(self):
        """Create a Job Template using input

        :id: dbaf5aa9-101d-47dc-bdf8-d5b4d1a52396

        :Steps:

            1. Navigate to Hosts -> Job Templates
            2. Enter a name
            3. Navigate to the job tab
            4. Enter a job name
            5. Click the +Add Input button
            6. Add an appropriate name
            7. Choose an input type
            8. Populate the template code and reference the newly created input
            9. Click submit

        :expectedresults: The job template was successfully saved with new
            input added

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        var_name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            self.jobtemplate.add_input(name, var_name)
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(var_name)
            )

    @tier1
    def test_negative_create_job_template(self):
        """Create Job Template with invalid name

        :id: 79342781-1369-4d1f-a512-ca1a809d98fb

        :Steps:

            1. Navigate to Hosts -> Job Templates
            2. Enter an invalid name
            3. Click submit

        :expectedresults: Job Template with invalid name cannot be created and
            error is raised

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_job_template(
                        session,
                        name=name,
                        template_type='input',
                        template_content=gen_string('alphanumeric', 20),
                    )
                    self.assertIsNotNone(self.jobtemplate.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_negative_create_job_template_with_same_name(self):
        """Create Job Template with duplicate name

        :id: 2c193758-dc34-4701-863c-f2823851223a

        :Steps:

            1. Create a new job template.
            2. Enter a name that has already been used
            3. Click submit

        :expectedresults: The name duplication is caught and error is raised

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.wait_until_element(
                common_locators['name_haserror']))

    @tier1
    @upgrade
    def test_positive_delete_job_template(self):
        """Delete a job template

        :id: b25e4fb9-ad75-407d-b15f-76df381c4f9c

        :Setup: Create a valid job template.

        :Steps:

            1. Click the dropdown next to the Job Template's Run button
            2. Select Delete from the list
            3. Confirm the deletion

        :expectedresults: The Job Template has been deleted

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.jobtemplate.delete(name, dropdown_present=True)

    @tier1
    @upgrade
    def test_positive_clone_job_template(self):
        """Clone a Job Template

        :id: a1ec5d1d-907f-4d18-93d3-adb1134d9cca

        :Setup: Create a valid job template.

        :Steps:

            1. Navigate to Hosts -> Job Templates
            2. Click the clone button next to a job template
            3. Change the name
            4. Click submit

        :expectedresults: Verify all job template contents were successfully
            copied

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        clone_name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alphanumeric', 20),
            )
            self.assertIsNotNone(self.jobtemplate.search(name))
            self.jobtemplate.clone(name, clone_name)
            self.assertIsNotNone(self.jobtemplate.search(clone_name))

    @tier1
    def test_positive_view_diff(self):
        """View diff within template editor

        :id: 4b8fff93-4862-4119-bb97-aadc50fc817d

        :Setup: Create a valid job template.

        :Steps:

            1. Open the job template created during setup
            2. Modify the template's code
            3. Click the Diff button

        :expectedresults: Verify that the new changes are displayed in the
            window

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        old_template = gen_string('alpha')
        new_template = gen_string('alphanumeric')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=old_template,
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.assign_value(
                locators['job.template_input'], new_template)
            self.jobtemplate.click(common_locators['ace.diff'])
            template_text = self.jobtemplate.wait_until_element(
                locators['job.template_input']).text
            self.assertIn('-' + old_template, template_text)
            self.assertIn('+' + new_template, template_text)

    @tier1
    def test_positive_preview_verify(self):
        """Use preview within the job template editor to verify template

        :id: 4b4939f3-c056-4716-8071-e8fa00233e3e

        :Steps:

            1. Create a new job template.
            2. Add input controls under jobs
            3. Reference those input controls in the template text
            4. Select "preview" within the template viewer

        :expectedresults: Verify no errors are thrown

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        var_name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alpha'),
                org=self.organization.name,
            )
            self.jobtemplate.add_input(name, var_name)
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(var_name)
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.click(common_locators['ace.preview'])
            self.assertEqual(
                u'$USER_INPUT[{0}]'.format(var_name),
                self.jobtemplate.wait_until_element(
                    locators['job.template_input']).text
            )

    @tier1
    def test_negative_preview_verify(self):
        """Use a template file to populate the job template

        :id: 8c0d132c-b500-44b5-a549-d32c7636a712

        :Steps:

            1. Create a new job template
            2. Add input controls under jobs
            3. Incorrectly reference those input controls in the template text
            4. And/or reference non-existent input controls in the template
               text
            5. Select "preview" within the template viewer

        :expectedresults: Verify appropriate errors are thrown

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=name,
                template_type='input',
                template_content=gen_string('alpha'),
                org=self.organization.name,
            )
            self.jobtemplate.add_input(name, gen_string('alpha'))
            self.jobtemplate.update(
                name,
                template_type='input',
                template_content='<%= input("{0}") %>'.format(
                    gen_string('alphanumeric'))
            )
            self.jobtemplate.click(self.jobtemplate.search(name))
            self.jobtemplate.click(common_locators['ace.preview'])
            self.assertIsNotNone(self.jobtemplate.wait_until_element(
                common_locators['alert.error']))

    @tier1
    def test_positive_preview_job_template_with_foreman_url(self):
        """Create a simple Job Template that contains foreman url variable in
        its body

        :id: 46f93efd-1508-41b6-af34-e9d7f658925b

        :Steps:

            1. Navigate to Hosts -> Job Templates
            2. Enter a valid name
            3. Populate the template code
            4. Navigate to the job tab
            5. Enter a job name
            6. Click submit
            7. Open created template and select "preview" within the template
                viewer

        :expectedresults: The job template content can be previewed without
            errors

        :BZ: 1374344

        :CaseImportance: Critical
        """
        template_name = gen_string('alpha')
        with Session(self) as session:
            make_job_template(
                session,
                name=template_name,
                template_type='input',
                template_content='<%= foreman_url("built") %>',
            )
            self.jobtemplate.click(self.jobtemplate.search(template_name))
            self.jobtemplate.click(common_locators['ace.preview'])
            self.assertIn(
                settings.server.hostname,
                self.jobtemplate.wait_until_element(
                    locators['job.template_input']).text
            )


class RemoteExecutionTestCase(UITestCase):
    """Test class for remote execution feature"""

    @classmethod
    @skip_if_not_set('clients', 'fake_manifest', 'vlan_networking')
    def setUpClass(cls):
        """Create an organization which can be re-used in tests."""
        super(RemoteExecutionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()
        cls.new_sub = entities.Subnet(
            domain=[entities.Domain(id=1)],
            gateway=settings.vlan_networking.gateway,
            ipam='DHCP',
            location=[entities.Location(id=DEFAULT_LOC_ID)],
            mask=settings.vlan_networking.netmask,
            network=settings.vlan_networking.subnet,
            network_type='IPv4',
            remote_execution_proxy=[entities.SmartProxy(id=1)],
            organization=[cls.organization],
        ).create()

    def get_client_datetime(self):
        """Make Javascript call inside of browser session to get exact current
        date and time. In that way, we will be isolated from any issue that can
        happen due different environments where test automation code is
        executing and where browser session is opened. That should help us to
        have successful run for docker containers or separated virtual machines
        When calling .getMonth() you need to add +1 to display the correct
        month. Javascript count always starts at 0, so calling .getMonth() in
        May will return 4 and not 5.

        @return: Datetime object that contains data for current date and time
            on a client
        """
        script = ('var currentdate = new Date(); return ({0} + "-" + {1} + '
                  '"-" + {2} + " : " + {3} + ":" + {4});').format(
            'currentdate.getFullYear()',
            '(currentdate.getMonth()+1)',
            'currentdate.getDate()',
            'currentdate.getHours()',
            'currentdate.getMinutes()',
        )
        client_datetime = self.browser.execute_script(script)
        return datetime.strptime(client_datetime, '%Y-%m-%d : %H:%M')

    @stubbed()
    @tier2
    def test_positive_run_default_job_template(self):
        """Run a job template against a single host

        :id: 7f0cdd1a-c87c-4324-ae9c-dbc30abad217

        :Setup: Use pre-defined job template.

        :Steps:

            1. Navigate to an individual host and click Run Job
            2. Select the job and appropriate template
            3. Run the job

        :expectedresults: Verify the job was successfully ran against the host

        :CaseLevel: Integration
        """
        with VirtualMachine(
                distro=DISTRO_RHEL7,
                bridge=settings.vlan_networking.bridge,
                provisioning_server=settings.compute_resources.libvirt_hostname
                ) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            self.assertTrue(client.subscribed)
            add_remote_execution_ssh_key(client.ip_addr)
            Host.update({
                u'name': client.hostname,
                u'subnet-id': self.new_sub.id,
            })
            with Session(self) as session:
                set_context(session, org=self.organization.name)
                self.hosts.click(self.hosts.search(client.hostname))
                status = self.job.run(
                    job_category='Commands',
                    job_template='Run Command - SSH Default',
                    options_list=[{'name': 'command', 'value': 'ls'}]
                )
                # get job invocation id from the current url
                invocation_id = self.browser.current_url.rsplit('/', 1)[-1]
                try:
                    self.assertTrue(status)
                except AssertionError:
                    result = 'host output: {0}'.format(
                            ' '.join(JobInvocation.get_output({
                                'id': invocation_id,
                                'host': client.hostname})
                            )
                        )
                    raise AssertionError(result)

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel6_host(self):
        """Run a job against a single provisioned RHEL 6 host

        :id: 7cc94029-69a0-43e0-8ce5-fdf802d0addc

        :Setup:

            1. Provision a RHEL 6 host.
            2. Create a working job template.

        :Steps:

            1. Navigate to the provisioned host and click Run Job
            2. Select the created job and appropriate template
            3. Click submit

        :expectedresults: Verify the job was successfully ran on the
            provisioned host

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_run_job_against_provisioned_rhel7_host(self):
        """Run a job against a single provisioned RHEL 7 host

        :id: e911edfb-abcf-4ea2-940d-44f3e4de1954

        :Setup:

            1. Provision a RHEL 7 host.
            2. Create a working job template.

        :Steps:

            1. Navigate to the provisioned host and click Run Job
            2. Select the created job and appropriate template
            3. Click submit

        :expectedresults: Verify the job was successfully ran on the
            provisioned host

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_run_job_against_multiple_provisioned_hosts(self):
        """Run a job against multiple provisioned hosts

        :id: 7637f724-924f-478d-88d8-25f500335236

        :Setup:

            1. Provision at least two hosts (RHEL6/7 preferred).
            2. Create a working job template.

        :Steps:

            1. Navigate to the hosts page and select all provisioned hosts
            2. Click Select Action -> Run Job
            3. Select the created job and appropriate template
            4. Click submit

        :expectedresults: Verify the job was successfully ran on the
            provisioned hosts

        :caseautomation: notautomated

        :CaseLevel: System
        """

    @tier2
    def test_positive_run_default_job_template_by_ip(self):
        """Run a job template on a host connected by ip

        :id: 9a90aa9a-00b4-460e-b7e6-250360ee8e4d

        :Setup: Use pre-defined job template.

        :Steps:

            1. Set remote_execution_connect_by_ip on host to true
            2. Navigate to an individual host and click Run Job
            3. Select the job and appropriate template
            4. Run the job

        :expectedresults: Verify the job was successfully ran against the host

        :CaseLevel: Integration
        """
        with VirtualMachine(
              distro=DISTRO_RHEL7,
              provisioning_server=settings.compute_resources.libvirt_hostname,
              bridge=settings.vlan_networking.bridge,
              ) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            self.assertTrue(client.subscribed)
            add_remote_execution_ssh_key(client.ip_addr)
            Host.update({
                'name': client.hostname,
                'subnet-id': self.new_sub.id,
            })
            # connect to host by ip
            Host.set_parameter({
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            })
            with Session(self) as session:
                set_context(session, org=self.organization.name)
                self.hosts.click(self.hosts.search(client.hostname))
                status = self.job.run(
                    job_category='Commands',
                    job_template='Run Command - SSH Default',
                    options_list=[{'name': 'command', 'value': 'ls'}]
                )
                # get job invocation id from the current url
                invocation_id = self.browser.current_url.rsplit('/', 1)[-1]
                try:
                    self.assertTrue(status)
                except AssertionError:
                    result = 'host output: {0}'.format(
                            ' '.join(JobInvocation.get_output({
                                'id': invocation_id,
                                'host': client.hostname})
                            )
                        )
                    raise AssertionError(result)

    @tier3
    def test_positive_run_custom_job_template_by_ip(self):
        """Run a job template on a host connected by ip

        :id: e283ae09-8b14-4ce1-9a76-c1bbd511d58c

        :Setup: Create a working job template.

        :Steps:

            1. Set remote_execution_connect_by_ip on host to true
            2. Navigate to an individual host and click Run Job
            3. Select the job and appropriate template
            4. Run the job

        :expectedresults: Verify the job was successfully ran against the host

        :CaseLevel: System
        """
        jobs_template_name = gen_string('alpha')
        with VirtualMachine(
              distro=DISTRO_RHEL7,
              provisioning_server=settings.compute_resources.libvirt_hostname,
              bridge=settings.vlan_networking.bridge,
              ) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            self.assertTrue(client.subscribed)
            add_remote_execution_ssh_key(client.ip_addr)
            Host.update({
                'name': client.hostname,
                'subnet-id': self.new_sub.id,
            })
            # connect to host by ip
            Host.set_parameter({
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            })
            with Session(self) as session:
                set_context(session, org=self.organization.name)
                make_job_template(
                    session,
                    name=jobs_template_name,
                    template_type='input',
                    template_content='<%= input("command") %>',
                    provider_type='SSH',
                )
                self.assertIsNotNone(
                    self.jobtemplate.search(jobs_template_name))
                self.jobtemplate.add_input(
                    jobs_template_name, 'command', required=True)
                self.hosts.click(self.hosts.search(client.hostname))
                status = self.job.run(
                    job_category='Miscellaneous',
                    job_template=jobs_template_name,
                    options_list=[{'name': 'command', 'value': 'ls'}]
                )
                # get job invocation id from the current url
                invocation_id = self.browser.current_url.rsplit('/', 1)[-1]
                try:
                    self.assertTrue(status)
                except AssertionError:
                    result = 'host output: {0}'.format(
                            ' '.join(JobInvocation.get_output({
                                'id': invocation_id,
                                'host': client.hostname})
                            )
                        )
                    raise AssertionError(result)

    @upgrade
    @tier3
    def test_positive_run_job_template_multiple_hosts_by_ip(self):
        """Run a job template against multiple hosts by ip

        :id: c4439ec0-bb80-47f6-bc31-fa7193bfbeeb

        :Setup: Create a working job template.

        :Steps:

            1. Set remote_execution_connect_by_ip on hosts to true
            2. Navigate to the hosts page and select at least two hosts
            3. Click the "Select Action"
            4. Select the job and appropriate template
            5. Run the job

        :expectedresults: Verify the job was successfully ran against the hosts

        :CaseLevel: System
        """
        prov_server = settings.compute_resources.libvirt_hostname
        with VirtualMachine(
              distro=DISTRO_RHEL7,
              provisioning_server=prov_server,
              bridge=settings.vlan_networking.bridge,
              ) as client:
            with VirtualMachine(
                  distro=DISTRO_RHEL7,
                  provisioning_server=prov_server,
                  bridge=settings.vlan_networking.bridge,
                  ) as client2:
                for vm in client, client2:
                    vm.install_katello_ca()
                    vm.register_contenthost(
                        self.organization.label, lce='Library')
                    self.assertTrue(vm.subscribed)
                    add_remote_execution_ssh_key(vm.ip_addr)
                    Host.update({
                        'name': vm.hostname,
                        'subnet-id': self.new_sub.id,
                    })
                    # connect to host by ip
                    Host.set_parameter({
                        'host': vm.hostname,
                        'name': 'remote_execution_connect_by_ip',
                        'value': 'True',
                    })
                with Session(self) as session:
                    set_context(session, org=self.organization.name)
                    self.hosts.update_host_bulkactions(
                        [client.hostname, client2.hostname],
                        action='Schedule Remote Job',
                        parameters_list=[{'command': 'ls'}],
                    )
                    strategy, value = locators['job_invocation.status']
                    if self.job.wait_until_element(
                            (strategy, value % 'succeeded'), 240) is not None:
                        status = True
                    else:
                        status = False
                    # get job invocation id from the current url
                    invocation_id = self.browser.current_url.rsplit('/', 1)[-1]
                    try:
                        self.assertTrue(status)
                    except AssertionError:
                        result = 'host output: {0}'.format(
                                ' '.join(JobInvocation.get_output({
                                     'id': invocation_id,
                                     'host': client.hostname})
                                )
                            )
                        raise AssertionError(result)

    @tier3
    def test_positive_run_scheduled_job_template_by_ip(self):
        """Schedule a job to be ran against a host by ip

        :id: 4387bed9-969d-45fb-80c2-b0905bb7f1bd

        :Setup: Use pre-defined job template.

        :Steps:

            1. Set remote_execution_connect_by_ip on host to true
            2. Navigate to an individual host and click Run Job
            3. Select the job and appropriate template
            4. Select "Schedule Future Job"
            5. Enter a desired time for the job to run
            6. Click submit

        :expectedresults:

            1. Verify the job was not immediately ran
            2. Verify the job was successfully ran after the designated time

        :CaseLevel: System
        """
        with VirtualMachine(
              distro=DISTRO_RHEL7,
              provisioning_server=settings.compute_resources.libvirt_hostname,
              bridge=settings.vlan_networking.bridge,
              ) as client:
            client.install_katello_ca()
            client.register_contenthost(self.organization.label, lce='Library')
            self.assertTrue(client.subscribed)
            add_remote_execution_ssh_key(client.ip_addr)
            Host.update({
                'name': client.hostname,
                'subnet-id': self.new_sub.id,
            })
            # connect to host by ip
            Host.set_parameter({
                'host': client.hostname,
                'name': 'remote_execution_connect_by_ip',
                'value': 'True',
            })
            with Session(self) as session:
                set_context(session, org=self.organization.name)
                self.hosts.click(self.hosts.search(client.hostname))
                plan_time = (
                        self.get_client_datetime() + timedelta(seconds=180)
                        ).strftime("%Y-%m-%d %H:%M")
                status = self.job.run(
                    job_category='Commands',
                    job_template='Run Command - SSH Default',
                    options_list=[{'name': 'command', 'value': 'ls'}],
                    schedule='future',
                    schedule_options=[
                        {'name': 'start_at', 'value': plan_time}],
                    result='queued to start executing in 1 minute'
                )
                self.assertTrue(status)
                strategy, value = locators['job_invocation.status']
                self.job.wait_until_element_is_not_visible(
                    (strategy, value % 'queued'), 95)
                if self.job.wait_until_element(
                        (strategy, value % 'succeeded'), 180) is not None:
                    status2 = True
                else:
                    status2 = False
                # get job invocation id from the current url
                invocation_id = self.browser.current_url.rsplit('/', 1)[-1]
                try:
                    self.assertTrue(status2)
                except AssertionError:
                    result = 'host output: {0}'.format(
                            ' '.join(JobInvocation.get_output({
                                'id': invocation_id,
                                'host': client.hostname})
                            )
                        )
                    raise AssertionError(result)
