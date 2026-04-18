# InsureVision AI

InsureVision AI is a **fully integrated Python project** that combines **GenAI**, **Agentic AI**, and **DevOps** patterns in one demo-ready application. A FastAPI backend powers a **single-page black-themed frontend** with tab navigation, while Terraform, Docker, Kubernetes manifests, and GitHub Actions document a realistic path from laptop to AWS.

## Modules

1. **GenAI** — Users describe any insurance topic; the backend calls **Groq** (`llama-3.1-8b-instant`) for a clear multi-paragraph explanation and builds a **Pollinations.ai** image URL for a matching infographic-style visual.
2. **Agentic AI** — Three **separate Groq calls** (no CrewAI/LangChain): an insurance plan finder (strict JSON), a hospital finder (strict JSON), and a comparison writer. JSON is parsed safely with **try/except** and **hardcoded fallbacks** if the model returns invalid JSON so demos never break.
3. **DevOps** — **Docker** image for the API, **docker-compose** for local runs, **Terraform** for an EC2 `t2.micro` plus security group, **Kubernetes** Deployment/Service samples, and **GitHub Actions** CI/CD that tests, builds, and applies Terraform on pushes to `main`.

## Prerequisites

- **Python** 3.11+
- **Docker** and Docker Compose (optional but recommended for local container runs)
- **Terraform** 1.6+ (for AWS provisioning)
- **AWS account** with credentials capable of creating EC2 and security groups
- **Groq API key** from [Groq Console](https://console.groq.com/)

## Local setup (Python)

1. Clone the repository and enter the project root (`InsureVision-AI/`).
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `GROQ_API_KEY`.
4. From the **project root** (the folder that contains `backend/` and `frontend/`):

   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Open **http://localhost:8000** — the UI is served from `frontend/index.html` at `/`. API calls use the **same origin** (e.g. `http://localhost:8000/api/...`), so the same build works when you later browse **`http://<EC2_PUBLIC_IP>:8000`** on AWS.

## Run with Docker (local)

From the project root:

```bash
docker compose -f devops/docker-compose.yml up --build
```

Ensure `.env` exists at the project root (compose references `../.env` relative to `devops/`). Then visit **http://localhost:8000**.

## Deploy on AWS with Terraform

1. Edit `devops/terraform/user_data.sh` and replace `YOUR_USERNAME` with your GitHub username (or fork URL) so EC2 can clone the repo.
2. Set `key_name` in `devops/terraform/variables.tf` (or pass `-var 'key_name=your-key'`) to an existing key pair in the target region.
3. Confirm the **AMI** matches your region (`ami_id` default is for **us-east-1**).
4. Export AWS credentials and (optionally) pass your Groq key for user data:

   ```powershell
   $env:AWS_ACCESS_KEY_ID="..."
   $env:AWS_SECRET_ACCESS_KEY="..."
   $env:TF_VAR_groq_api_key="your_groq_key"
   ```

5. Run Terraform:

   ```bash
   cd devops/terraform
   terraform init
   terraform plan
   terraform apply
   ```

6. After apply completes, open **`http://<output_public_ip>:8000`** (see `outputs.tf` for `public_ip` and `app_url`).

### Destroy AWS resources

```bash
cd devops/terraform
terraform destroy
```

## Kubernetes deployment (outline)

1. Build and push `insurevision-ai:latest` to a registry your cluster can pull from (update `devops/k8s/deployment.yaml` image if needed).
2. Create a secret with your Groq key:

   ```bash
   kubectl create secret generic groq-secret --from-literal=GROQ_API_KEY=your_groq_api_key_here
   ```

3. Apply manifests:

   ```bash
   kubectl apply -f devops/k8s/deployment.yaml
   kubectl apply -f devops/k8s/service.yaml
   ```

The Deployment runs **3 replicas** with a **RollingUpdate** (`maxUnavailable: 0`). The Service type is **NodePort** on **30080**.

## API endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/` | — | `frontend/index.html` |
| `GET` | `/health` | — | `{ "status": "ok" }` |
| `POST` | `/api/genai` | `{ "query": string }` | `{ "text": string, "image_url": string }` |
| `POST` | `/api/agent` | `{ "age": int, "city": string, "budget": int, "type": string }` | `{ "plans": [...], "hospitals": [...], "comparison": string, "recommendation": string }` |

## Architecture (ASCII)

```
[Browser]
    |
    v
[ FastAPI :8000 ] ----> [ Groq API ]  (GenAI + agents)
    |
    +--> Pollinations (image URL only; browser loads image)

DevOps path:

[Developer] -> [git push main]
        |
        v
[GitHub Actions: pip / pytest / docker build / terraform apply]
        |
        v
[Terraform AWS Provider]
        |
        v
[EC2 t2.micro + SG :22 :8000]
        |
        v
[user_data: Docker install -> git clone -> docker build -> docker run]
        |
        v
[App URL: http://<PUBLIC_IP>:8000]
```

## GitHub Actions secrets

Configure these in the repository **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | Terraform AWS provider authentication |
| `AWS_SECRET_ACCESS_KEY` | Terraform AWS provider authentication |
| `GROQ_API_KEY` | Passed as `TF_VAR_groq_api_key` for EC2 `user_data` `.env` generation (optional if you manage keys another way) |

**Security note:** Putting API keys in Terraform `user_data` is convenient for coursework demos but is **not** ideal for production; prefer AWS Secrets Manager or SSM Parameter Store for real workloads.

## Tests

```bash
pip install pytest httpx
python -m pytest
```

`pytest.ini` sets `pythonpath = .` so `from backend.main import app` resolves.

## License

Use and modify freely for learning and demos.
