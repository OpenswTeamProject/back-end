# Back-end Server

**Open SW Team Project** - Backend API Server  
서비스 배포 및 실행에 대한 가이드입니다.

## 🔧 실행 방법

GCP의 **k3s 엔진**을 사용하여 서비스를 배포하였습니다. 아래의 명령어를 통해 Kubernetes 클러스터에서 배포 상태를 확인하고 서비스를 실행할 수 있습니다.

### Kubernetes 배포 명령어
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

### 외부 접속
- NodePort 설정을 활용하여 **31234 포트**를 통해 외부 접속이 가능합니다.
- 다음 URL로 API 명세서를 확인할 수 있습니다:
  - **http://34.64.194.23:31234**

### 로컬에서 실행
만약 GCP의 서버가 꺼져 있거나 Minikube를 통해 배포된 경우, **31234 포트**를 사용하여 로컬 환경에서도 접속할 수 있습니다.

## 📜 API 명세서
API 명세서는 Swagger UI를 통해 제공됩니다.  
위의 외부 접속 URL로 접속하여 API의 동작을 직접 테스트할 수 있습니다.

## 🙋‍♂️ 문의
- **팀 이름**: Open SW Team06  
- **이메일**: OpenSWTeam06@gmail.com  
