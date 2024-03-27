- Epic Name: Preprocessing: Backend Pipeline manager
	Bigger tool: Preprocessing: Pipeline manager
- DESC: Backend Pipeline manager to execute in the sequence all the stand-alone tools


- Components: CloudBuild
- iGPM MCR BM number: BM-00086032_004
- Problems statements:
	+) Stand-alone tools available for preprocessing shall be executed in a pipeline according to a specific sequence.
	+) Preferred common location for outputs from different tools.
	+) Last step will consist in merging all the changes in PVER then update the catalog to de/register files before starting SW Build.

- Requirement:
	+) 001: As a Integrator I want to execute a manual script in RSB workspace to execute the complete RSB PreProcessing pipeline locally
	+) 002: As a Integrator I want to execute an automation script in RSB Back-End to execute the complete RSB PreProcessing pipeline in the RSB Back-End environment


- Links of cloud tools:
	https://rb-artifactory.bosch.com/artifactory/dgs-ec-psa-ci-local/cloud_services/remotesharedbuild/tools/

- Name of release: release/ECPT-11693-preprocessing-backend-pipeline-manager


- Pre-requisites:
1. IN_PVER: PVER from CI-dashboard
2. IN_STLA: STLA inputs from RSB inputs
3. TOOL and TOOL_configuration

- Sequence:
1. MICConfigurator
	a. input: IN_STLA
	b. output: OUT_MIC
2. Float32Updater
	a. input: OUT_MIC/STLA_ASW
	b. output: OUT_MIC/STLA_ASW (same folder)
3. ConfManager
	a. input: IN_PVER, OUT_MIC, TOOL_configuration
	b. output: OUT_ConfUpdator
4. TiSchedUpdater
	a. input: OUT_MIC/Rte, IN_PVER/TISCHED
	b. output: OUT_TISCHED
5. StubGenerator
	a. input: OUT_MIC/STLA_ASW
	b. output: OUT_STUB
6. ComStubSelector
	a. input: TOOL_configuration details: IN_PVER, OUT_MIC
	b. output: <TOOL_path>\output\
7. NvMStubSelector
	a. input: TOOL_configuration details: IN_PVER, OUT_MIC
	b. output: c:\users\<nt-user_id>\.temp\
8. SoftwareMerger
	a. input: TOOL_configuration details: OUT_MIC, OUT_ConfUpdator, OUT_TISCHED, OUT_STUB, OUT_COMSTUB, OUT_NVMSTUB, IN_PVER,
	b. output: IN_PVER
9. CatalogUpdater
	a. input: IN_PVER