import os
import shutil
import zipfile
from datetime import *
from logger.loadlogconf import LoadLogconf

folder_path = input('\nEnter the folder path where zips are placed: ')
dest_path = input('Enter the destination path where tools are placed: ')  
java_jre = input('Enter java.exe path: ')

logger = LoadLogconf(logger_choice="dev").log
logger.info("START PIPELINE")

################### Functions used in the stand-alone tools ###################
def copy_files(src,dst, pattern_start, pattern_end):
    if not os.path.exists(dst):
        logger.info('Create folder: ',dst)
        os.makedirs(dst)
    for file in os.listdir(src):
        if (file.endswith(pattern_end) & file.startswith(pattern_start)):
            filesrc = os.path.join(src, file)
            filedst = os.path.join(dst, file)
            logger.info("Copy: ",filesrc)
            shutil.copy(filesrc, filedst)

def backup_file(file):
    if os.path.exists(file):
        logger.info('Rename file: '+ file + " as .bak")
        if os.path.exists(file + '.bak'):
            logger.info('Already existing: ' + file + '.bak')
        else:
            os.rename(file, file + '.bak')

def backup_files(dst,ext):
    if os.path.exists(dst):
        for file in os.listdir(dst):
            if (file.endswith(ext)):
                filename = os.path.join(dst, file)
                logger.info('Rename file: '+ filename + " as .bak")
                if os.path.exists(filename + '.bak'):
                    logger.info('Already existing: ' + filename + '.bak')
                else:
                    os.rename(filename, filename + '.bak')      

################### Function for getting remote-build tools ###################                
def unzip_remote_tool(folder_path, dest_path):
    for file in os.listdir(folder_path): 
        file_path = os.path.join(folder_path, file) 

        if file.endswith('.zip'):            
            tool_folder_name = file.split('-')[0]
            logger.info("==================================================================================")          
            logger.info(f'Extracting {file}...') 
                   
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_contents = zip_ref.namelist()
                # If zip file already contains the same-named folder in
                if (tool_folder_name + '/' in zip_contents):                
                    zip_ref.extractall(dest_path)
                    logger.info(f"Extracted contents of {file} to folder {dest_path}{tool_folder_name}")
                # Create a folder if zip file doesn't have one inside it
                else:                     
                    tool_folder = os.path.join(dest_path, tool_folder_name)
                    if not os.path.exists(tool_folder):
                        os.mkdir(tool_folder)                
                        zip_ref.extractall(tool_folder)
                        logger.info(f"Extracted contents of {file} to folder {tool_folder}")
     
unzip_remote_tool(folder_path, dest_path)   
logger.info('================== Finished unzip archive of remotebuild tool ==================') 
                         
################### Remote build tools #################################
# Sequence: MICConfigurator - Float32Updater - ConfManager - TiSchedUpdater - StubGenerator 
# - ComStubSelector - NvMStubSelector - SoftwareMerger - CatalogUpdater
stla_path = input('\nEnter the input path of STLA: ')
rb_pver = input('Enter Pver path: ')
micconfigurator_output = os.path.join(dest_path, 'Outputs/MICConfigurator/')

def micconfigurator():
    # MIC Configurator
    logger.info('1. MIC Configurator')
    if not os.path.exists(micconfigurator_output):
        os.makedirs(micconfigurator_output)

    path = os.path.join(dest_path, 'MICConfigurator')
    cmd = path + '/MICConfigurator.exe -i ' + stla_path + " -o " + micconfigurator_output
    logger.info(cmd)
    os.system(cmd)

def float32updator():
    # Float32 Updator
    logger.info('2. Float32 Updator')
    float32_input = os.path.join(micconfigurator_output, 'RSB_Inputs/ApplicationComponents/')
    if not os.path.exists(float32_input):
        os.makedirs(float32_input)
    
    path = os.path.join(dest_path, 'Float32Updater')
    cmd = path + '/Preprocess-Float32Updater.exe -i ' + float32_input
    logger.info(cmd)
    os.system(cmd)

def confmanager():
    # Conf Updator
    # -m "Updater"
    # -p /path/to/pver/root
    # -ws /path/to/cust/ws
    # -cf path/to/configuration/file
    # -o /path/to/output/folder
    logger.info('3. ConfManager')
    tool_path = os.path.join(dest_path, 'ConfManager/ConfManager.exe')
    mode = 'Merger'
    pver_path = rb_pver
    conf_path = os.path.join(dest_path, 'ConfManager/ConfManager_merger.json')

    output = os.path.join(dest_path, 'Outputs/ConfUpdator/')
    if not os.path.exists(output):
        os.makedirs(output)
    cmd = tool_path + ' -m ' + mode + ' -p ' + pver_path + ' -cf ' + conf_path + ' -o ' + output
    logger.info(cmd)
    os.system(cmd)

def tischedupdator():
    # TiSched Updator
    # XML_SCHED_PATH
    # TISCHED_PATH
    # CLEAN_TISCHED
    # dedicated Folder for RTE to reduce list of ARXML files otherwise it fails
    # file to be ignored for InitialExport => rba_Swc_Scl_Rte_EcucValues.arxml
    logger.info('4. TISCHEDUpdator')
    output_folder = os.path.join(dest_path, 'Outputs/TiSchedUpdator/')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    xml_sched_path = os.path.join(micconfigurator_output, 'RSB_Inputs/RB_RteArch_T4_AH')
    if not os.path.exists(xml_sched_path):
        os.makedirs(xml_sched_path)
    
    tisched_updator_path = os.path.join(dest_path, 'TiSchedUpdater/TiSchedUpdater_1.5.0')
    if not os.path.exists(tisched_updator_path):
        os.makedirs(tisched_updator_path)

    cmd = tisched_updator_path + '/XmlToXlsSched.exe -s ' + xml_sched_path + ' -o ' + output_folder
    logger.info(cmd)
    os.system(cmd)

    headless_qvto_path = os.path.join(tisched_updator_path, 'TiSchedUpdaterqvtoHeadless.jar')
    qvto_filename = os.path.join(tisched_updator_path,'transforms/ExcelToTisched.qvto')
    tisched_path = rb_pver + "/Conf/OS_Shell/rba_osarschedextn_schedcfg.tisched"

    cmd = java_jre + ' -jar ' + headless_qvto_path \
        + ' -transformationPath ' + qvto_filename \
        + ' -inputs ' + output_folder + '/scheduling_db.xlsx ' \
        + tisched_path \
        + ' -Dpriority_to_constraint=false -Dclean_tisched=true'
    logger.info(cmd)
    os.system(cmd)

def stubgenerator():
    # Stub generator
    # StubGenerator.exe -asw /path/to/Application/Components/folder -o /path/to/output/folder
    logger.info('5. StubGenerator')    
    tool_path = os.path.join(dest_path, 'StubGenerator/StubGenerator.exe')
    asw_path = os.path.join(dest_path, 'Outputs/MICConfigurator/RSB_Inputs/ApplicationComponents')
    output_folder = os.path.join(dest_path, 'Outputs/StubGenerator/')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)       
    cmd = tool_path + ' -asw ' + asw_path + ' -o ' + output_folder
    logger.info(cmd)
    os.system(cmd)

def comstubselector():
    logger.info('6. ComStubSelector')
    tool_path = os.path.join(dest_path, 'ComStubSelector/ComStubSelector.exe')
    conf_path = os.path.join(dest_path, 'ComStubSelector/configuration.json')
    cmd = tool_path + ' --conf ' + conf_path
    logger.info(cmd)
    os.system(cmd)

def nvmstubselector():
    logger.info('7. NvmStubSelector')
    tool_path = os.path.join(dest_path, 'NvmStubSelector/NvmStubSelector.exe')
    conf_path = os.path.join(dest_path, 'NvMStubSelector/configuration.json')
    cmd = tool_path + ' --json ' + conf_path + ' --PVERpath ' + rb_pver
    logger.info(cmd)
    os.system(cmd)

def swmerger():
    # Software Merger
    # softwareMerger.exe -p /path/to/pver -c /path/to/configFile
    logger.info('8. SoftwareMerger')
    tool_path = os.path.join(dest_path, 'SoftwareMerger/SoftwareMerger_1.0.0.exe')
    conf_path = os.path.join(dest_path, 'SoftwareMerger/configuration.json')
    cmd = tool_path + ' -p ' + rb_pver + ' -c ' + conf_path

    logger.info(cmd)
    os.system(cmd)
    #ToDO: once catalog updator is updated to de-register files
    backup_file(rb_pver + '/SwSAStellantis/__SwSAStellantis/swsastellantis_adapter_fca_sharedinterfaces.arxml')
    backup_file(rb_pver + '/SwSStellantis/Adpr_SwSStellantis/swsstellantis_FCADataDefinition.arxml')
    backup_files(rb_pver + '/SwSStellantis/IF_SwSStellantis/IF_SwSStellantis/IF_SwSStellantis/','arxml')
    backup_file(rb_pver + '/Conf/__Conf/conf_rootproject_mg1.arxml')

def catalogupdator():
    # Catalog Updator
    logger.info('9. CatalogUpdater')
    tool_path = os.path.join(dest_path, 'CatalogUpdater/CatalogUpdater1.0.0.jar')
    cmd = java_jre + ' -jar ' + tool_path + ' ' + rb_pver
    logger.info(cmd)
    os.system(cmd)

def launch_all_tools():
    micconfigurator()
    float32updator()
    confmanager()
    tischedupdator()
    stubgenerator()
    comstubselector()
    nvmstubselector()
    swmerger()
    catalogupdator()

launch_all_tools()
logger.info("END PIPELINE")
