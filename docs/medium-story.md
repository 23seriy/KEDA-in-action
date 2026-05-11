# KEDA in Action: Event-Driven Autoscaling on Your Laptop
 
 Most Kubernetes autoscaling demos start with CPU or memory. That is understandable because those signals are built into the platform and easy to chart. But from an operator’s point of view, those metrics are often only **proxies** for real demand.
 
 If your system processes work from a queue, the question is not “Are my pods hot enough to scale?” The real question is “**Is work piling up faster than I can drain it?**”
 
 That is where KEDA becomes genuinely useful.
 
 In this article, I want to show KEDA through a story that is both practical and fun: an **NBA fan platform** that generates highlight packages, stat cards, and game recap assets when live-game moments create sudden spikes in demand. Think of a tight Lakers-Celtics game, a fourth-quarter run, and a flood of requests for fresh basketball content. The API is lightweight and only enqueues jobs. The expensive work happens in background workers. When nothing is happening, we want **zero workers**. When game-night traffic hits, we want Kubernetes to scale up quickly and safely.
 
 That is a much more honest scaling model than “CPU above 70% means maybe scale out.”
 
 ## Why DevOps Engineers Should Care
 
 After two decades in DevOps, one pattern remains constant: the best autoscaling strategy is the one that follows the shape of the workload as closely as possible.
 
 CPU-based autoscaling is indirect.
 Queue-based autoscaling is intent-driven.
 
 For queue consumers, queue depth tells you what you actually need to know:
 
 - **Are users or downstream systems waiting?**
 - **Is backlog growing?**
 - **Do I need capacity now, not after CPU catches up?**
 
 KEDA lets you scale on those first-class operational signals.
 
 ## Demo Architecture
 
 This project has only a few moving parts, which is exactly what makes it good for teaching.
 
 - **Producer API**
   - accepts basketball-content jobs
   - pushes them into Redis
 
 - **Redis queue**
   - stores the pending workload
   - acts as the event source for scaling
 
 - **Worker deployment**
   - pulls jobs from Redis
   - simulates content processing
 
 - **KEDA ScaledObject**
   - watches queue depth
   - scales the worker deployment up and down
 
 ### Architecture Illustration
 
 ```text
                       ┌────────────────────────────────────────────┐
                       │            Minikube / Kubernetes           │
                       │                                            │
 NBA fan traffic ───►  │  Producer API ───────► Redis queue         │
 localhost:9090        │      │                highlight-jobs       │
                       │      │                                     │
                       │      └──── submit highlight/stat jobs      │
                       │                                            │
                       │            KEDA watches queue length       │
                       │                     │                      │
                       │                     ▼                      │
                       │          Worker Deployment (0 → N)         │
                       │                                            │
                       └────────────────────────────────────────────┘
 ```
 
 ### Suggested Illustration for Medium
 
 - **Screenshot 1**
   - Minikube cluster running
   - `kubectl get pods -A`
 
 - **Screenshot 2**
   - producer UI open at `http://localhost:9090`
   - buttons for submitting highlight jobs visible
 
 - **Screenshot 3**
   - terminal showing `kubectl get pods -n keda-demo -l app=worker -w`
   - worker pods scaling up after a burst
 
 - **Screenshot 4**
   - `kubectl get scaledobject -n keda-demo`
   - queue-driven scaler visible
 
 ## Step 1: Install the Tooling
 
 First, make the helper scripts executable and install the local dependencies.
 
 ```bash
 chmod +x scripts/*.sh
 ./scripts/01-install-prerequisites.sh
 ```
 
 This verifies or installs:
 
 - `minikube`
 - `kubectl`
 - `helm`
 - `docker`
 
 ### What to show in the article
 
 Add a terminal screenshot of the script confirming the toolchain is available. DevOps readers like seeing evidence that the setup is reproducible.
 
 ## Step 2: Start the Cluster and Install KEDA
 
 Next, bring up the local cluster and install KEDA.
 
 ```bash
 ./scripts/02-start-cluster.sh
 ```
 
 This script:
 
 - creates a Minikube profile named `keda-demo`
 - starts Kubernetes `v1.32.0`
 - installs KEDA using Helm
 - waits for the KEDA operator to become ready
 
 Verify the cluster state:
 
 ```bash
 kubectl get nodes
 kubectl get pods -n keda
 ```
 
 You should see the KEDA operator and metrics apiserver running.
 
 ### Suggested illustration
 
 ```text
 $ kubectl get pods -n keda
 NAME                                              READY   STATUS    RESTARTS   AGE
 keda-operator-xxxxxxxxxx-xxxxx                    1/1     Running   0          40s
 keda-operator-metrics-apiserver-xxxxxxxxx-xxxxx   1/1     Running   0          40s
 ```
 
 ## Step 3: Deploy the Basketball Demo
 
 Now deploy the Redis queue, producer API, worker deployment, and default KEDA scaler.
 
 ```bash
 ./scripts/03-deploy-app.sh
 ```
 
 This script does three important things that are worth calling out in the article:
 
 - builds images directly inside the Minikube Docker daemon
 - deploys the application into the `keda-demo` namespace
 - applies the default `ScaledObject`
 
 Validate what was created:
 
 ```bash
 kubectl get all -n keda-demo
 kubectl get scaledobject -n keda-demo
 ```
 
 At this point, you should have:
 
 - a Redis deployment and service
 - a producer deployment and service
 - a worker deployment
 - a KEDA `ScaledObject`
 
 ### Operational note
 
 This is the moment where I usually tell readers to pause and inspect the state before generating load. A big part of DevOps maturity is learning to establish a clean baseline before testing dynamic behavior.
 
 ## Step 4: Open the Producer API
 
 In a second terminal, port-forward the producer service.
 
 ```bash
 kubectl port-forward svc/producer 9090:8080 -n keda-demo
 ```
 
 Then open:
 
 - `http://localhost:9090/`
 - `http://localhost:9090/status`
 
 The UI gives you a simple way to submit basketball-content jobs into the queue.
 
 ### Suggested illustration
 
 Capture the browser page with:
 
 - the queue length cards
 - the job buttons
 - the raw status JSON block
 
 That visual makes the demo feel immediately more tangible.
 
 ## Step 5: Watch the Workers Before Generating Load
 
 Before clicking anything in the UI, open a terminal and watch the worker pods.
 
 ```bash
 kubectl get pods -n keda-demo -l app=worker -w
 ```
 
 If the queue is empty, this is where the story becomes compelling: **there may be no worker pods at all**. That is not failure. That is the design.
 
 This is one of the best ways to explain KEDA to skeptical operators. The absence of idle workers is not fragility. It is efficiency.
 
 ## Step 6: Run the Default Demo Scenario
 
 Submit a burst of jobs from the UI, or use the guided scenario script.
 
 ```bash
 ./scripts/04-demo-scenarios.sh
 ```
 
 The first scenario applies the default Redis scaler threshold and sends a burst of jobs into the queue.
 
 If you prefer to narrate the steps manually in the article, do this:
 
 ```bash
 kubectl apply -f keda/scaledobject-queue-5.yaml
 curl -s -X POST http://localhost:9090/enqueue \
   -H "Content-Type: application/json" \
   -d '{"count": 25, "processing_time": 5}'
 ```
 
 Then watch:
 
 ```bash
 kubectl get pods -n keda-demo -l app=worker -w
 ```
 
 You should see workers come online as the highlight backlog grows.
 
 ### What to explain to DevOps readers
 
 Emphasize that KEDA is not reacting to CPU saturation here. It is reacting to queued work. That difference matters in real systems because backlog is often visible **before** resource pressure becomes obvious.
 
 ## Step 7: Explore the Scaling Profiles
 
 This is where the article can move from demo to engineering judgment.
 
 ### Scenario A: Default threshold of 5
 
 ```bash
 kubectl apply -f keda/scaledobject-queue-5.yaml
 ```
 
 Use this when:
 
 - fan wait time matters
 - jobs are moderately expensive
 - you want visibly responsive scaling
 
 ### Scenario B: Conservative threshold of 20
 
 ```bash
 kubectl apply -f keda/scaledobject-queue-20.yaml
 ```
 
 This profile tolerates more backlog before adding capacity aggressively.
 
 Use this when:
 
 - infrastructure cost matters more than immediate responsiveness
 - jobs are short-lived
 - queue delay is acceptable
 
 ### Scenario C: Fast polling and shorter cooldown
 
 ```bash
 kubectl apply -f keda/scaledobject-fast-polling.yaml
 ```
 
 This profile is better for sharp spikes, such as a sudden wave of requests after a buzzer-beater or viral highlight.
 
 Use this section to explain the operational tradeoff:
 
 - faster response
 - faster scale down
 - higher chance of noisy scaling if the workload is bursty and irregular
 
 ### Scenario D: Cron pre-warm plus queue trigger
 
 ```bash
 kubectl apply -f keda/scaledobject-cron-warm.yaml
 ```
 
 This is one of the most realistic patterns in production.
 
 If you already know the NBA evening slate starts at predictable times, pre-warm a baseline number of workers, then let queue depth scale further when demand exceeds expectations.
 
 That combination of **predictable scaling** and **event-driven scaling** is far closer to real platform operations than a one-dimensional autoscaling rule.
 
 ## Step 8: Verify Scale to Zero
 
 One of the most important moments in the demo comes after the spike.
 
 Stop submitting jobs and keep watching the worker deployment:
 
 ```bash
 kubectl get deploy worker -n keda-demo -w
 ```
 
 Or inspect the queue directly through the status endpoint:
 
 ```bash
 curl -s http://localhost:9090/status | jq
 ```
 
 As backlog drains, KEDA should scale the worker deployment back down.
 
 This is the point I would explicitly call out in the article with a screenshot pair:
 
 - **before burst:** zero workers
 - **during burst:** multiple workers
 - **after drain:** back to zero
 
 That three-stage visual sequence sells the concept better than any abstract definition.
 
 ## What This Demo Teaches Beyond the Happy Path
 
 Small demos are useful when they trigger the right production questions.
 
 This one should make readers ask:
 
 - What is the most truthful scaling signal for my workload?
 - How quickly should I react to demand?
 - What backlog is acceptable for my users?
 - How long should I wait before scaling back down?
 - Should I pre-warm capacity for known peaks?
 - What is the cost of being wrong in either direction?
 
 Those are the questions that separate a demo from an operating model.
 
 ## Writing Notes for Medium Publication
 
 If you publish this on Medium, I recommend structuring the final article with these visual beats:
 
 - **Hero section**
   - title
   - one-sentence promise
   - architecture illustration
 
 - **Setup section**
   - one screenshot of tooling
   - one screenshot of KEDA installed
 
 - **Live demo section**
   - producer UI screenshot
   - worker scaling terminal screenshot
   - `ScaledObject` manifest snippet
 
 - **Operational insights section**
   - explain thresholds, cooldown, and polling interval
   - compare queue-driven vs CPU-driven thinking
 
 - **Final takeaway**
   - one concise paragraph on why KEDA matters in real systems
 
 ## Final Takeaway
 
 KEDA is compelling because it makes autoscaling feel closer to application intent.
 
 Instead of asking Kubernetes to infer demand from resource pressure, you can teach it to react to signals your platform already understands: queue backlog, scheduled spikes, cloud messages, Kafka lag, or database activity.
 
 For this demo, the signal is basketball-content backlog.
 
 In a real platform, that backlog could represent orders, messages, videos, ETL tasks, alerts, or event streams.
 
 The principle stays the same:
 
 **scale based on the thing your users are actually waiting for.**
