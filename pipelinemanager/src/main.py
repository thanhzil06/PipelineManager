import argparse
import json
import os
import shutil
import zipfile

from logger import loadlogconf


class PipelineExecutor:
    """
    ************ Functions used in the stand-alone tools **********************
    """

    def __init__(self, params):
        self.logger = loadlogconf.LoadLogconf('dev').get_logger()
        if params.interactive:
            self.tool_folder = input('Enter the folder path where zips are placed: ')
            self.dest_path = input('Enter the folder path where output will be placed: ')
            self.stla_path = input('Enter the input path of STLA: ')
            self.conf_path = input('Enter the conf file path: ')
            self.rb_pver = input('Enter Pver path: ')
        else:
            self.tool_folder = params.tool_path
            self.dest_path = params.dest_path
            self.stla_path = params.input_path
            self.conf_path = params.conf_path
            self.rb_pver = params.pver_path

        self.workspace = os.path.join(self.dest_path, 'workspace/')
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

    def copy_files(self, src, dst, pattern_start, pattern_end) -> None:
        """
        Method that copy tools and files to the specified folder
        :param src:
        :param dst:
        :param pattern_start:
        :param pattern_end:
        :return:
        """
        if not os.path.exists(dst):
            self.logger.info('Create folder: ', dst)
            os.makedirs(dst)
        for file in os.listdir(src):
            if file.endswith(pattern_end) & file.startswith(pattern_start):
                file_src = os.path.join(src, file)
                file_dst = os.path.join(dst, file)
                self.logger.info("Copy: ", file_src)
                shutil.copy(file_src, file_dst)

    def backup_file(self, file) -> None:
        if os.path.exists(file):
            self.logger.info('Rename file: ' + file + " as .bak")
            if os.path.exists(file + '.bak'):
                self.logger.info('Already existing: ' + file + '.bak')
            else:
                os.rename(file, file + '.bak')

    def backup_files(self, dst, ext) -> None:
        if os.path.exists(dst):
            for file in os.listdir(dst):
                if file.endswith(ext):
                    filename = os.path.join(dst, file)
                    self.logger.info('Rename file: ' + filename + " as .bak")
                    if os.path.exists(filename + '.bak'):
                        self.logger.info('Already existing: ' + filename + '.bak')
                    else:
                        os.rename(filename, filename + '.bak')

                    # ************** Function for getting remote-build tools ****************#

    def unzip_remote_tool(self) -> None:
        """
        Unzip tools archive that are downloaded from Artifactory
        :return: None
        """
        for file in os.listdir(self.tool_folder):
            file_path = os.path.join(self.tool_folder, file)

            if file.endswith('.zip'):
                tool_folder_name = file.split('-')[0]
                self.logger.info("==================================================================================")
                self.logger.info(f'Extracting {file}...')

                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_contents = zip_ref.namelist()
                    # If zip file already contains the same-named folder in
                    if tool_folder_name + '/' in zip_contents:
                        zip_ref.extractall(self.dest_path)
                        self.logger.info(f"Extracted contents of {file} to folder {self.dest_path}{tool_folder_name}")
                    # Create a folder if zip file doesn't have one inside it
                    else:
                        tool_folder = os.path.join(self.dest_path, tool_folder_name)
                        if not os.path.exists(tool_folder):
                            os.mkdir(tool_folder)
                            zip_ref.extractall(tool_folder)
                            self.logger.info(f"Extracted contents of {file} to folder {tool_folder}")

    def micconfigurator(self) -> None:
        """
        Method that launches MicConfigurator tool
        :return: None
        """
        self.logger.info('1. MIC Configurator')

        path = os.path.join(self.dest_path, 'MICConfigurator')
        cmd = path + '/MICConfigurator.exe -i ' + self.stla_path + " -o " + self.workspace
        self.logger.info(cmd)
        os.system(cmd)

    def float32_updator(self) -> None:
        """
        Method that launches Float32Updater tool
        :return: None
        """
        self.logger.info('2. Float32 Updator')
        float32_input = os.path.join(self.workspace, 'RSB_Inputs/ApplicationComponents')
        path = os.path.join(self.dest_path, 'Float32Updater')
        cmd = path + '/Preprocess-Float32Updater.exe -i ' + float32_input
        self.logger.info(cmd)
        os.system(cmd)

    def conf_manager(self) -> None:
        """
        Method that launches ConfManager tool
        -m "Updater"
        -p /path/to/pver/root
        -ws /path/to/cust/ws
        -cf path/to/configuration/file
        -o /path/to/output/folder
        :return: None
        """
        self.logger.info('3. ConfManager')
        tool_path = os.path.join(self.dest_path, 'ConfManager/ConfManager.exe')
        mode = 'Merger'
        pver_path = self.rb_pver
        conf_path = os.path.join(self.conf_path, 'ConfManager_merger.json')

        cmd = tool_path + ' -m ' + mode + ' -p ' + pver_path + ' -cf ' + conf_path + ' -o ' + self.workspace
        self.logger.info(cmd)
        os.system(cmd)

    def tisched_updater(self) -> None:
        """
        Method that launches TiSchedUpdater tool
         XML_SCHED_PATH
        TISCHED_PATH
        CLEAN_TISCHED
        dedicated Folder for RTE to reduce list of ARXML files otherwise it fails
        file to be ignored for InitialExport => rb
        a_Swc_Scl_Rte_EcucValues.arxml
        :return: None
        """
        self.logger.info('4. TISCHEDUpdator')
        output_folder = os.path.join(self.dest_path, 'TiSchedUpdater/')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        xml_sched_path = os.path.join(self.workspace, 'RSB_Inputs/RB_RteArch_T4_AH')
        if not os.path.exists(xml_sched_path):
            os.makedirs(xml_sched_path)

        tisched_updator_path = os.path.join(self.dest_path, 'TiSchedUpdater/TiSchedUpdater_1.5.0')
        if not os.path.exists(tisched_updator_path):
            os.makedirs(tisched_updator_path)

        cmd = tisched_updator_path + '/XmlToXlsSched.exe -s ' + xml_sched_path + ' -o ' + output_folder
        self.logger.info(cmd)
        os.system(cmd)

        headless_qvto_path = os.path.join(tisched_updator_path, 'TiSchedUpdaterqvtoHeadless.jar')
        qvto_filename = os.path.join(tisched_updator_path, 'transforms/ExcelToTisched.qvto')
        tisched_path = self.rb_pver + "/Conf/OS_Shell/rba_osarschedextn_schedcfg.tisched"

        cmd = 'C:\\toolbase\\java_jre\\11.0.12_64\\bin\\java.exe -jar ' + headless_qvto_path + ' -transformationPath ' \
              + qvto_filename + ' -inputs ' + output_folder + '/scheduling_db.xlsx ' + tisched_path + \
              ' -Dpriority_to_constraint=false -Dclean_tisched=true'
        self.logger.info(cmd)
        os.system(cmd)

    def stub_generator(self) -> None:
        """
        Method that launches StubGenerator tool
        StubGenerator.exe -asw /path/to/Application/Components/folder -o /path/to/output/folder
        :return: None
        """
        self.logger.info('5. StubGenerator')
        tool_path = os.path.join(self.dest_path, 'StubGenerator/StubGenerator.exe')
        asw_path = os.path.join(self.workspace, 'RSB_Inputs/ApplicationComponents')
        output_folder = os.path.join(self.workspace, 'StubGenerator/')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        cmd = tool_path + ' -asw ' + asw_path + ' -o ' + output_folder
        self.logger.info(cmd)
        os.system(cmd)

    def modify_configuration_file(self, conf_path) -> None:
        """
        Method to modify the path of the configuration file for NvmStubSelector and ComStubSelector
        :param conf_path: path to configuration json file
        :return: None
        """
        with open(conf_path, "r") as json_configuration_file:
            conf_data = json.load(json_configuration_file)
        if conf_data:
            conf_data["path"]["pathToPVER"] = self.rb_pver
            conf_data["path"]["pathToSTLAFiles"] = self.workspace
        with open(conf_path, "w") as json_configuration_file:
            json.dump(conf_data, json_configuration_file)

    def com_stub_selector(self) -> None:
        """
        Method that launches ComStubSelector tool
        :return: None
        """
        self.logger.info('6. ComStubSelector')
        tool_path = os.path.join(self.dest_path, 'ComStubSelector/ComStubSelector.exe')
        conf_path = os.path.join(self.conf_path, 'comstubselector_configuration.json')
        self.modify_configuration_file(conf_path)
        cmd = tool_path + ' --conf ' + conf_path
        self.logger.info(cmd)
        os.system(cmd)
        com_stub_selector_output_path = os.path.join(self.dest_path,
                                                     'ComStubSelector/output/comcil_adapt_ess_rte_stub.c')
        shutil.copy(com_stub_selector_output_path, os.path.join(self.workspace, 'comcil_adapt_ess_rte_stub.c'))

    def nvm_stub_selector(self) -> None:
        """
        Method that launches NvmStubSelector tool
        :return: None
        """
        self.logger.info('7. NvmStubSelector')
        tool_path = os.path.join(self.dest_path, 'NvmStubSelector/NvmStubSelector.exe')
        conf_path = os.path.join(self.conf_path, 'nvmstubselector_configuration.json')
        self.modify_configuration_file(conf_path)
        cmd = tool_path + ' --json ' + conf_path + ' --PVERpath ' + self.rb_pver
        self.logger.info(cmd)
        os.system(cmd)
        # copy output to workspace
        user_path = os.path.expanduser('~')
        nvm_stub_selector_output = os.path.normpath(os.path.join(f'{user_path}/.temp/output', 'nvm_swadp.c'))
        shutil.copy(nvm_stub_selector_output, os.path.join(self.workspace, 'nvm_swadp.c'))

    def software_merger(self) -> None:
        """
        Method that launches SoftwareMerger tool
        softwareMerger.exe -p /path/to/pver -c /path/to/configFile
        :return: None
        """
        self.logger.info('8. SoftwareMerger')
        tool_path = os.path.join(self.dest_path, 'SoftwareMerger/SoftwareMerger.exe')
        conf_path = os.path.join(self.conf_path, 'swmerger_configuration.json')
        cmd = tool_path + ' -p ' + self.rb_pver + ' -c ' + conf_path

        self.logger.info(cmd)
        os.system(cmd)
        self.backup_file(
            self.rb_pver + '/SwSAStellantis/__SwSAStellantis/swsastellantis_adapter_fca_sharedinterfaces.arxml')
        self.backup_file(self.rb_pver + '/SwSStellantis/Adpr_SwSStellantis/swsstellantis_FCADataDefinition.arxml')
        self.backup_files(self.rb_pver + '/SwSStellantis/IF_SwSStellantis/IF_SwSStellantis/IF_SwSStellantis/', 'arxml')
        self.backup_file(self.rb_pver + '/Conf/__Conf/conf_rootproject_mg1.arxml')

    def catalog_updator(self) -> None:
        """
        Methode that launch the catalogUpdater
        :return: None
        """
        self.logger.info('9. CatalogUpdater')
        tool_path = os.path.join(self.dest_path, 'CatalogUpdater/CatalogUpdater.jar')
        conf_path = os.path.join(self.conf_path, 'catalogupdater_configuration.json')
        cmd = "C:\\toolbase\\java_jre\\11.0.12_64\\bin\\java.exe -jar " + tool_path + ' ' + self.rb_pver + \
              ' ' + conf_path
        self.logger.info(cmd)
        os.system(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', help='tool folder', required=False, dest='tool_path')
    parser.add_argument('-o', '--out', help='spec path', required=False, dest='dest_path')
    parser.add_argument('-in', '--input', help='input path', required=False, dest='input_path')
    parser.add_argument('-c', '--conf', help='configuration files path', required=False, dest='conf_path')
    parser.add_argument('-pver', '--pver', help='pver path', required=False, dest='pver_path')
    parser.add_argument('-i', '--interactive', help='interactive mode', required=False, dest='interactive')
    args = parser.parse_args()

    pipeline_process = PipelineExecutor(args)
    pipeline_process.unzip_remote_tool()

    # ********************* Remote build tools ******************************** #
    # Sequence: MICConfigurator - Float32Updater - ConfManager - TiSchedUpdater - StubGenerator
    # - ComStubSelector - NvMStubSelector - SoftwareMerger - CatalogUpdater

    pipeline_process.micconfigurator()
    pipeline_process.float32_updator()
    pipeline_process.conf_manager()
    pipeline_process.tisched_updater()
    pipeline_process.stub_generator()
    pipeline_process.com_stub_selector()
    pipeline_process.nvm_stub_selector()
    pipeline_process.software_merger()
    pipeline_process.catalog_updator()
