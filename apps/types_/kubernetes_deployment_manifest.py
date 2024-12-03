import subprocess
import uuid
from datetime import datetime

import kubernetes_validate
import yaml
import yaml.scanner


class KubernetesDeploymentManifest:
    """Represents a k8s deployment manifest"""

    _deployment_id = None
    _manifest_content = None

    def __init__(self, override_deployment_id: str = None):
        if override_deployment_id:
            self._deployment_id = override_deployment_id
        else:
            # Generate and set a unique deployment id
            # Example pattern: "20241126_085112_02500f53-7435-49a2-a5c2-66443e677a33"
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._deployment_id = f"{now}_{str(uuid.uuid4())}"

    def get_filepaths(self) -> dict[str, str]:
        """Returns two filepaths for this deployment for the values file and deployment file."""
        deployment_fileid = self.get_deployment_id()
        values_file = f"charts/values/{deployment_fileid}.yaml"
        deployment_file = f"charts/values/{deployment_fileid}_deployment.yaml"
        _paths = {"values_file": values_file, "deployment_file": deployment_file}
        return _paths

    def get_deployment_id(self) -> str:
        """Gets the unique deployment id"""
        return self._deployment_id

    def save_as_values_file(self, values_data: str) -> None:
        """Saves values data to a yaml file."""
        values_file = self.get_filepaths()["values_file"]
        with open(values_file, "w") as f:
            f.write(values_data)

    def generate_manifest_yaml_from_template(
        self, chart: str, values_file: str, namespace: str, version: str = None, save_to_file: bool = False
    ) -> tuple[str | None, str | None]:
        """
        Generate the manifest yaml for this deployment.
        The Helm command should be run as a Celery task but Celery lacks support for class methods.
        Therefore we import the Helm command function from the tasks module.
        When run in unit tests, this needs to use syncronously using CELERY_ALWAYS_EAGER
        """

        from ..tasks import helm_template

        output, error = helm_template(chart, values_file, namespace, version)

        if not error:
            if save_to_file:
                deployment_file = self.get_filepaths()["deployment_file"]
                with open(deployment_file, "w") as f:
                    f.write(output)

        return output, error

    def _delete_deployment_file(self) -> None:
        """Removes the deployment file if it exist."""
        files = self.kdm.get_filepaths()
        from pathlib import Path

        deployment_file = files["deployment_file"]

        if Path(deployment_file).is_file():
            subprocess.run(["rm", "-f", deployment_file])

    def validate_manifest(self, manifest_data: str) -> dict[bool, str]:
        """
        Validates manifest documents for this deployment.
        Uses kubernetes-validate to validate in-memory.

        Returns:
        dict[bool,str]: is_valid, output
        """
        invalid_docs = []

        # Parse the yaml manifest into multiple documents
        try:
            documents = list(yaml.safe_load_all(manifest_data))
        except yaml.scanner.ScannerError as e:
            return False, f"Unable to parse manifest yaml. ScannerError. {e}"
        except Exception as e:
            return False, f"Unable to parse manifest yaml. {e}"

        # Now validate each manifest document
        for doc in documents:
            try:
                print(f"Validating document {doc['kind']}")

                kubernetes_validate.validate(doc, "1.28", strict=True)

            except kubernetes_validate.ValidationError as e:
                invalid_docs.append(doc["kind"])
                print(f"The kubernetes-validate tool found errors: {e}")

            except Exception as e:
                invalid_docs.append(doc["kind"])
                print(f"An error occurred during validation: {e}")

        output = f"Nr of docs with errors {len(invalid_docs)} of {len(documents)}"
        print(output)

        is_valid = len(invalid_docs) == 0

        return is_valid, output

    def extract_kubernetes_pod_patches_from_manifest(self, manifest_data: str) -> str | None:
        """
        Extracts a section of the manifest yaml known as kubernetes-pod-patches.

        Returns:
        str: The subset text or None if not found in the manifest data.
        Throws:
        yaml.scanner.ScannerError if unable to parse yaml
        """
        start_index = manifest_data.find("kubernetes-pod-patches")

        if start_index == -1:
            return None

        # Extract the kubernetes-pod-patches data from the YAML data
        # Parse the yaml manifest into multiple documents
        documents = list(yaml.safe_load_all(manifest_data))

        # Search for the kubernetes-pod-patches section
        for doc in documents:
            if doc["kind"] == "ConfigMap":
                application_yml_data = doc.get("data", {}).get("application.yml")

                if application_yml_data:
                    application_config = yaml.safe_load(application_yml_data)
                    proxy_data = application_config.get("proxy")

                    if proxy_data:
                        specs_data = proxy_data.get("specs")

                        if specs_data:
                            kubernetes_pod_patches_data = None
                            for spec in specs_data:
                                kubernetes_pod_patches_data = spec.get("kubernetes-pod-patches")
                                if kubernetes_pod_patches_data:
                                    return kubernetes_pod_patches_data.strip()

        return None

    def validate_kubernetes_pod_patches_yaml(self, input: str) -> dict[bool, str]:
        """
        Validates the kubernetes-pod-patches section.

        Returns:
        dict[bool,str]: is_valid, message
        """

        try:
            kubernetes_pod_patches = yaml.safe_load(input)

            if not isinstance(kubernetes_pod_patches, list):
                return False, "kubernetes-pod-patches should be a list"

        except yaml.YAMLError as e:
            return False, f"kubernetes-pod-patches is invalid YAML: {e}"
        except ValueError as e:
            return False, f"kubernetes-pod-patches is invalid: {e}"

        return True, None

    def _validate_manifest_file(self) -> dict[bool, str, str]:
        """
        Validates the manifest file for this deployment.
        Note: This does not appear to be working, but kept for continued testing.

        Returns:
        dict[bool,str,str]: is_valid, output, validation_error
        """
        from ..tasks import kubectl_apply_dry

        output, error = kubectl_apply_dry(self.get_filepaths()["deployment_file"], target_strategy="client")

        if error:
            return False, output, error

        if output is not None and "error:" in output:
            return False, output, error

        return True, output, error

    def check_helm_version(self) -> tuple[str | None, str | None]:
        """Verifies that the Helm CLI is installed and accessible."""

        command = "helm version"
        # Execute the command
        try:
            result = subprocess.run(command.split(" "), check=True, text=True, capture_output=True)
            return result.stdout, None
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr
