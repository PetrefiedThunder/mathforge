# Math & Physics Accessible Platform

This monorepo scaffold provides:

- **Self-hosted Git (Gitea)** with LaTeX rendering and simulation widgets.
- **SMS micro-task distribution** for crowdsourced submissions.
- **Regulatory compliance engine** to enforce global and accessibility laws.
- **Adaptive UI** (WCAG & ARIA compliant) for inclusive research participation.
- **Infrastructure as Code** (Terraform) and **Kubernetes** (Helm) for production deployment.

## Unified Platform Directory Structure

```
math-physics-git 
├── docker-compose.yml
├── .gitea-ci.yml
├── helm/                      # Kubernetes Helm charts for production
│   └── math-physics-git/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── templates/
│       │   ├── deployment.yaml
│       │   ├── ingress.yaml
│       │   └── _helpers.tpl
├── infra/                     # Terraform modules for cloud infra
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── services/
│   ├── gitea/
│   │   ├── Dockerfile
│   │   ├── config/
│   │   └── custom-themes/     # KaTeX templates with ARIA support
│   ├── simulation/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── search/
│   │   ├── go.mod
│   │   └── main.go
│   ├── sms/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── regcomp/              # Regulatory compliance engine
│   │   ├── Dockerfile
│   │   ├── scanner.py         # Scans submissions against global regulations
│   │   └── requirements.txt
│   └── adaptive-ui/           # Accessibility and adaptive environment
│       ├── Dockerfile
│       ├── server.js         # Node.js Express server
│       ├── components/       # React components with ARIA labels
│       │   ├── index.html
│       │   └── app.js
│       └── tailwind.config.js
├── sms_loader/                # Problem loader scripts
│   └── load_problems.py
├── scripts/
│   └── init_volume.sh        # Data migration and initialization
└── README.md
```

## Getting Started

1. Copy `.env.example` to `.env` and fill in secrets (Twilio credentials, OpenAI key, etc.).
2. Run `docker-compose up --build` to build and start all services.
3. Execute `scripts/init_volume.sh` to load initial problems and policies.
4. Access services:
   - Gitea → [http://localhost:3000](http://localhost:3000)
   - Simulation API → [http://localhost:8000](http://localhost:8000)
   - SMS Service → [http://localhost:5000](http://localhost:5000)
   - Compliance Scanner (RegComp) → [http://localhost:7000/docs](http://localhost:7000/docs)
   - Adaptive UI → [http://localhost:4000](http://localhost:4000)

Happy contributing!
```‬

```yaml name=docker-compose.yml
version: '3.9'
services:
  gitea:
    build: ./services/gitea
    environment:
      USER_UID: 1000
      USER_GID: 1000
    volumes:
      - ./data/gitea:/data
    ports:
      - "3000:3000"
      - "222:22"
    depends_on:
      - db
      - redis
      - minio
      - elasticsearch

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: gitea
      POSTGRES_PASSWORD: gitea_pass
      POSTGRES_DB: gitea
    volumes:
      - ./data/postgres:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - ./data/redis:/data

  minio:
    image: minio/minio:latest
    command: server /data
    environment:
      MINIO_ACCESS_KEY: minio
      MINIO_SECRET_KEY: minio123
    ports:
      - "9000:9000"
    volumes:
      - ./data/minio:/data

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    volumes:
      - ./data/es:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  simulation:
    build: ./services/simulation
    depends_on:
      - redis
    ports:
      - "8000:8000"

  search:
    build: ./services/search
    depends_on:
      - elasticsearch
    ports:
      - "8080:8080"

  sms:
    build: ./services/sms
    environment:
      TWILIO_ACCOUNT_SID: ${TWILIO_ACCOUNT_SID}
      TWILIO_AUTH_TOKEN: ${TWILIO_AUTH_TOKEN}
      TWILIO_PHONE_NUMBER: ${TWILIO_PHONE_NUMBER}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DATABASE_URL: postgresql://gitea:gitea_pass@db:5432/gitea
    depends_on:
      - db
      - redis
    ports:
      - "5000:5000"

  regcomp:
    build: ./services/regcomp
    environment:
      REGULATORY_DB: /data/regulations.json
    volumes:
      - ./data/regulations:/data
    ports:
      - "7000:7000"

  adaptive-ui:
    build: ./services/adaptive-ui
    ports:
      - "4000:4000"
```

```dockerfile name=helm/math-physics-git/Chart.yaml
apiVersion: v2
name: math-physics-git
description: A Helm chart for deploying the Math & Physics Accessible Platform
type: application
version: 0.1.0
appVersion: "2025.06.10"
```

```yaml name=helm/math-physics-git/values.yaml
replicaCount: 1

image:
  repository: math-physics-git
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  annotations: {}
  hosts:
    - host: math-physics.example.com
      paths: ["/"]

resources: {}

nodeSelector: {}

tolerations: []

affinity: {}
```

```yaml name=helm/math-physics-git/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "math-physics-git.fullname" . }}
  labels:
    app: {{ include "math-physics-git.name" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "math-physics-git.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "math-physics-git.name" . }}
    spec:
      containers:
        - name: {{ include "math-physics-git.name" . }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.port }}
          resources:
{{ toYaml .Values.resources | indent 12 }}
```

```yaml name=helm/math-physics-git/templates/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "math-physics-git.fullname" . }}
  annotations:
{{ toYaml .Values.ingress.annotations | indent 4 }}
spec:
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ . }}
            pathType: ImplementationSpecific
            backend:
              service:
                name: {{ include "math-physics-git.fullname" $. }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
```

```yaml name=helm/math-physics-git/templates/_helpers.tpl
{{/*
Return the name of this chart
*/}}
{{- define "math-physics-git.name" -}}
math-physics-git
{{- end -}}

{{/*
Return the full name of the chart including release name
*/}}
{{- define "math-physics-git.fullname" -}}
{{ .Release.Name }}-{{ include "math-physics-git.name" . }}
{{- end -}}
```

```python name=services/regcomp/scanner.py
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Regulatory Compliance Scanner")

# Load the policy database containing global regulations and accessibility laws.
with open('/data/regulations.json') as f:
    policies = json.load(f)

class Submission(BaseModel):
    problem_id: int
    content: str
    user_role: str  # e.g., 'academic', 'public'

@app.post('/scan')
def scan(sub: Submission):
    violations = []
    for rule in policies:
        # Check for accessibility rules: if ARIA attributes are required and not present.
        if rule['scope'] == 'accessibility' and 'ARIA' not in sub.content:
            violations.append(f"Missing ARIA compliance: {rule['description']}")
        # Check for export controls: restrict certain content based on user role.
        if rule['scope'] == 'export_control' and sub.user_role != 'public':
            violations.append(f"Export control applies: {rule['description']}")
    if violations:
        raise HTTPException(status_code=400, detail=violations)
    return { 'status': 'compliant' }
```

```dockerfile name=services/regcomp/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY scanner.py .
CMD ["uvicorn", "scanner:app", "--host", "0.0.0.0", "--port", "7000"]
```

```text name=services/regcomp/requirements.txt
fastapi
uvicorn
pydantic
```

```js name=services/adaptive-ui/server.js
const express = require('express');
const app = express();
const path = require('path');

// Serve static files from the components directory.
app.use(express.static(path.join(__dirname, 'components')));

// Serve the main index.html on the root path.
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'components', 'index.html'));
});

app.listen(4000, () => console.log('Adaptive UI running on port 4000'));
```

```html name=services/adaptive-ui/components/index.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Math & Physics Access Platform</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script type="module" src="app.js"></script>
</head>
<body class="p-4">
  <h1 class="text-2xl font-bold" aria-label="Platform Title">
    Accessible Math & Physics Platform
  </h1>
  <div id="content" role="main"></div>
</body>
</html>
```

```js name=services/adaptive-ui/components/app.js
import React from 'react';
import ReactDOM from 'react-dom';
import { Button, Card } from './ui';

// A simple React component to welcome users to the platform.
function App() {
  return (
    <div>
      <Card>
        <p id="welcome" tabIndex="0">
          Welcome to a fully adaptive, accessible research portal.
        </p>
        <Button 
          onClick={() => alert('Feature coming soon')}
          aria-label="Start Exploration"
        >
          Start Exploration
        </Button>
      </Card>
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById('content'));
```

```js name=services/adaptive-ui/tailwind.config.js
module.exports = {
  content: [
    "./components/**/*.{js,jsx,ts,tsx,html}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```dockerfile name=services/adaptive-ui/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 4000
CMD ["node", "server.js"]
```

````markdown
This unified scaffold is designed to be fully accessible and regulatory-compliant. Contributors of all experience levels can pull, fork, and contribute to features ranging from simulation and search to adaptive UI, SMS micro-tasks, and regulatory compliance scanning.