"""
IBM Quantum Runtime connection and job submission helpers.

Credentials are read from environment variables -- never hardcode an API
token in source control. Set these before running any hardware script
(see .env.example):

    IBM_QUANTUM_TOKEN     - your IBM Quantum API token
    IBM_QUANTUM_INSTANCE  - your IBM Cloud CRN / instance string
    IBM_QUANTUM_ACCOUNT   - (optional) saved-account name, default "dqft"
"""

import os

from qiskit.circuit import IfElseOp
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler


def get_runtime_service(account_name: str | None = None) -> QiskitRuntimeService:
    """
    Return a QiskitRuntimeService, saving a new named account from the
    IBM_QUANTUM_TOKEN / IBM_QUANTUM_INSTANCE environment variables on first
    use, or reusing a previously saved account of the same name.

    Args:
        account_name: name under which the account is saved locally.
            Defaults to the IBM_QUANTUM_ACCOUNT env var, or "dqft".

    Raises:
        RuntimeError: if no saved account exists and the required
            environment variables are not set.
    """
    account_name = account_name or os.environ.get("IBM_QUANTUM_ACCOUNT", "dqft")

    try:
        return QiskitRuntimeService(name=account_name)
    except Exception:
        token = os.environ.get("IBM_QUANTUM_TOKEN")
        instance = os.environ.get("IBM_QUANTUM_INSTANCE")
        if not token or not instance:
            raise RuntimeError(
                "No saved IBM Quantum account named "
                f"'{account_name}' was found, and IBM_QUANTUM_TOKEN / "
                "IBM_QUANTUM_INSTANCE are not set. Copy .env.example to .env, "
                "fill in your credentials, and load it before running this script."
            )
        QiskitRuntimeService.save_account(token=token, instance=instance, name=account_name)
        return QiskitRuntimeService(name=account_name)


def get_sampler(service: QiskitRuntimeService, backend_name: str) -> Sampler:
    """
    Return a configured SamplerV2 primitive bound to the given backend,
    with the experimental execution path and `if_else` instruction support
    needed for the mid-circuit feed-forward corrections in the e-bit
    gadgets.
    """
    backend = service.backend(backend_name)
    sampler = Sampler(mode=backend)
    sampler.options.experimental = {"execution_path": "gen3-experimental"}
    backend.target.add_instruction(IfElseOp, name="if_else")
    return sampler


def submit_circuits(sampler: Sampler, circuits: list, shots: int = 200):
    """Submit a batch of transpiled circuits to hardware and return the job."""
    job = sampler.run(pubs=circuits, shots=shots)
    print(f"Submitted job: {job.job_id()}")
    return job


def fetch_job_result(service: QiskitRuntimeService, job_id: str):
    """Retrieve the result of a previously submitted job by its job ID."""
    return service.job(job_id).result()
