# back-end
Open SW Team Project - Backend API server

---

### 실행 방법
GCP내의 k3s엔진을 활용해서 서비스 배포 완료했습니다.
```angular2html
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```
쿠버네티스의 NodePort 설정을 활용해서 외부 접속 포트를 만들었습니다
외부 접속 포트는 31234입니다

즉 http://34.64.194.23:31234 로 접속시 API 명세서 화면이 나옵니다.

만약 서버가 꺼진 경우나 minikube를 활용해서 접속시에는 
31234포트로 로컬에서도 원할하게 접속 가능합니다.