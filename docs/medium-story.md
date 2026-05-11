# KEDA in Action: Building Event-Driven Autoscaling Demos with Kubernetes, Redis, RabbitMQ, and an NBA Theme
 
 > A practical, DevOps-focused walkthrough of KEDA using basketball-content pipelines you can run on your laptop.
 
 **Estimated read time:** 10-12 minutes
 
 Most Kubernetes autoscaling demos begin with CPU or memory. That makes sense because those signals are built into the platform, easy to graph, and familiar to most engineers. But from an operator's point of view, those metrics are often only **proxies** for real demand.
 
 If your system processes work from a queue, the question is not “Are my pods hot enough to scale?” The real question is “**Is work piling up faster than I can drain it?**”
 
 That is where KEDA becomes genuinely useful.
 
 In this article, I want to show KEDA through a scenario that is both practical and memorable: an **NBA fan platform** that generates highlight packages, stat cards, and game recap assets when live-game moments create sudden spikes in demand. Think of a tight Lakers-Celtics game, a fourth-quarter run, and a flood of requests for fresh basketball content. The API is lightweight and only enqueues jobs. The expensive work happens later, inside worker pods. When nothing is happening, we want **zero workers**. When game-night traffic hits, we want Kubernetes to bring workers off the bench quickly and safely.
 
 That is a much more honest scaling model than “CPU above 70% means maybe scale out.”
 
 By the end of this walkthrough, you will have a complete local demo showing how KEDA scales from queue depth, how to switch between scaling policies, how `TriggerAuthentication` fits into a more realistic setup, and why event-driven autoscaling often maps better to real systems than CPU-only rules.
 
 ## Why DevOps Engineers Should Care
 
 After two decades in DevOps, one pattern remains constant: the best autoscaling strategy is the one that follows the shape of the workload as closely as possible.
 
 CPU-based autoscaling is indirect.
 Queue-based autoscaling is intent-driven.
 
 For queue consumers, queue depth tells you what you actually need to know:
 
 - **Are users or downstream systems waiting?**
 - **Is backlog growing?**
 - **Do I need capacity now, not after CPU catches up?**
 
 KEDA lets you scale on those first-class operational signals.
 
 That is why KEDA tends to click immediately with platform engineers. It does not ask you to invent synthetic thresholds first. It starts with a simpler question: *what does demand actually look like for this system?*
 
 ## The Demo Architecture
 
 This project has only a few moving parts, which is exactly what makes it useful for teaching and easy to reason about during a live demo.
 
 - **Producer API**
   - accepts basketball-content jobs
   - pushes them into Redis

 - **Redis queue**
   - stores the pending highlight workload
   - acts as the first event source for scaling

 - **RabbitMQ queue**
   - stores recap-batch workload
   - demonstrates a second, authenticated scaler path

 - **Worker deployments**
   - `worker` consumes Redis highlight jobs
   - `rabbit-worker` consumes RabbitMQ recap jobs

 - **KEDA ScaledObjects**
   - watch queue depth
   - scale the matching deployments up and down
 
 ### Architecture Illustration
 
 ```text
                       ┌────────────────────────────────────────────┐
                       │            Minikube / Kubernetes           │
                       │                                            │
                      │  Producer API ───────► Redis queue         │
 localhost:9090        │      │                highlight-jobs       │
                      │      │                                     │
                      │      └──── submit highlight/stat jobs      │
                      │                                            │
                      │  Rabbit publisher Job ─► RabbitMQ queue    │
                      │                        recap-jobs           │
                      │                                            │
                      │   KEDA watches Redis and RabbitMQ depth    │
                      │                 │               │           │
                      │                 ▼               ▼           │
                      │      Worker Deployment   Rabbit Worker     │
                      │           (0 → N)            (0 → N)       │
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
   - both Redis and RabbitMQ scaler examples visible
 
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
 
 This is an important confidence check. Before talking about autoscaling behavior, make sure the control plane pieces that enable it are healthy.
 
 ### Suggested illustration
 
 ```text
 $ kubectl get pods -n keda
 NAME                                              READY   STATUS    RESTARTS   AGE
 keda-operator-xxxxxxxxxx-xxxxx                    1/1     Running   0          40s
 keda-operator-metrics-apiserver-xxxxxxxxx-xxxxx   1/1     Running   0          40s
 ```
 
 ## Step 3: Deploy the Basketball Demo
 
 Now deploy the Redis queue, RabbitMQ broker, producer API, worker deployments, and the default Redis-based KEDA scaler.
 
 ```bash
 ./scripts/03-deploy-app.sh
 ```
 
 This script does three important things that are worth calling out in the article:
 
 - builds images directly inside the Minikube Docker daemon
 - deploys the application into the `keda-demo` namespace
 - installs both Redis and RabbitMQ demo paths
 - applies the default Redis `ScaledObject`
 
 Validate what was created:
 
 ```bash
 kubectl get all -n keda-demo
 kubectl get scaledobject -n keda-demo
 ```
 
 At this point, you should have:
 
 - a Redis deployment and service
 - a RabbitMQ deployment and service
 - a producer deployment and service
 - a Redis worker deployment
 - a RabbitMQ worker deployment
 - a KEDA `ScaledObject`
 
 ### Operational note
 
 This is the moment where I usually tell readers to pause and inspect the state before generating load. A big part of DevOps maturity is learning to establish a clean baseline before testing dynamic behavior. If you skip the baseline, every later result becomes harder to interpret.
 
 ## Step 4: Open the Producer API
 
 In a second terminal, port-forward the producer service.
 
 ```bash
 kubectl port-forward svc/producer 9090:8080 -n keda-demo
 ```
 
 Then open:
 
 - `http://localhost:9090/`
 - `http://localhost:9090/status`
 
 The UI gives you a simple way to submit basketball-content jobs into the queue.
 
 From a storytelling perspective, this matters. Readers can now connect what they do in the browser to what Kubernetes does in the cluster.
 
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
 
 In many organizations, this is the mental shift that matters most. We stop treating a zero-replica state as suspicious and start treating it as a valid, cost-aware steady state.
 
 ## Step 6: Run the Default Demo Scenario
 
 Submit a burst of jobs from the UI, or use the guided scenario script.
 
 ```bash
 ./scripts/04-demo-scenarios.sh
 ```
 
 The first scenario applies the default Redis scaler threshold and sends a burst of jobs into the queue.
 
 Before applying a different scaling profile manually, remove any existing `ScaledObject` that already manages the `worker` deployment. KEDA allows only one `ScaledObject` per workload target.

 If you prefer to narrate the steps manually in the article, do this:

 ```bash
 kubectl delete scaledobject --all -n keda-demo
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
 
 This is the core demo moment. A user action becomes queue depth. Queue depth becomes replica count. Replica count becomes queue drain. It is a clean chain of cause and effect, which is exactly what makes KEDA such a strong teaching tool.
 
 ### What to explain to DevOps readers
 
 Emphasize that KEDA is not reacting to CPU saturation here. It is reacting to queued work. That difference matters in real systems because backlog is often visible **before** resource pressure becomes obvious.
 
 ## Step 7: Explore the Scaling Profiles
 
 This is where the article moves from simple demo mechanics to engineering judgment.
 
 ### Scenario A: Default threshold of 5

 ```bash
 kubectl delete scaledobject --all -n keda-demo
 kubectl apply -f keda/scaledobject-queue-5.yaml
 ```
 
 Use this when:
 
 - fan wait time matters
 - jobs are moderately expensive
 - you want visibly responsive scaling
 
 This is the profile I would use to introduce KEDA in a live session because the response is fast enough to be obvious without being chaotic.
 
 ### Scenario B: Conservative threshold of 20

 ```bash
 kubectl delete scaledobject --all -n keda-demo
 kubectl apply -f keda/scaledobject-queue-20.yaml
 ```
 
 This profile tolerates more backlog before adding capacity aggressively.
 
 Use this when:
 
 - infrastructure cost matters more than immediate responsiveness
 - jobs are short-lived
 - queue delay is acceptable
 
 This is a useful reminder that autoscaling is never just technical. It is a policy decision about what level of waiting your platform considers acceptable.
 
 ### Scenario C: Fast polling and shorter cooldown

 ```bash
 kubectl delete scaledobject --all -n keda-demo
 kubectl apply -f keda/scaledobject-fast-polling.yaml
 ```
 
 This profile is better for sharp spikes, such as a sudden wave of requests after a buzzer-beater or viral highlight.
 
 Use this section to explain the operational tradeoff:
 
 - faster response
 - faster scale down
 - higher chance of noisy scaling if the workload is bursty and irregular
 
 In production, this is where you start balancing responsiveness against churn. Faster is not always better if it creates unnecessary scaling noise.
 
 ### Scenario D: Cron pre-warm plus queue trigger

 ```bash
 kubectl delete scaledobject --all -n keda-demo
 kubectl apply -f keda/scaledobject-cron-warm.yaml
 ```
 
 This is one of the most realistic patterns in production.
 
 If you already know the NBA evening slate starts at predictable times, pre-warm a baseline number of workers, then let queue depth scale further when demand exceeds expectations.
 
 That combination of **predictable scaling** and **event-driven scaling** is far closer to real platform operations than a one-dimensional autoscaling rule.
 
 This is one of my favorite KEDA patterns because it reflects how real systems behave: some peaks are scheduled, others are emergent, and a good platform strategy accounts for both.

 ### Scenario E: RabbitMQ queue scaling with TriggerAuthentication

 ```bash
 kubectl apply -f keda/scaledobject-rabbitmq.yaml
 kubectl apply -f k8s/rabbit-publisher-job.yaml
 ```

 This is the part of the demo that moves closer to a production-style integration. Instead of using an inline connection string directly in the scaler metadata, the RabbitMQ example stores the host connection string in a Kubernetes `Secret` and references it through a `TriggerAuthentication`.

 That matters because most real systems are not scaling against an unauthenticated local service. They are scaling against something that requires credentials, network boundaries, or both.

 Watch the RabbitMQ worker pods separately:

 ```bash
 kubectl get pods -n keda-demo -l app=rabbit-worker -w
 kubectl get hpa -n keda-demo -w
 ```

 The flow is intentionally different from the Redis UI demo:

 - a Kubernetes Job publishes recap messages into RabbitMQ
 - KEDA reads RabbitMQ queue depth through the RabbitMQ scaler
 - `rabbit-worker` pods scale from zero based on backlog
 - once the queue drains, the deployment returns to zero after cooldown

 This example adds two valuable ideas to the project:

 - **another scaler type**, so readers do not assume KEDA is only for Redis-style queues
 - **TriggerAuthentication**, so the article shows how KEDA commonly accesses authenticated event sources
 
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
 
 If you are turning this into a Medium post, this is the section where a before/during/after image sequence will do more work than three extra paragraphs.
 
 ## What This Demo Teaches Beyond the Happy Path
 
 Small demos are useful when they trigger the right production questions.
 
 This one should make readers ask:
 
 - What is the most truthful scaling signal for my workload?
 - How quickly should I react to demand?
 - What backlog is acceptable for my users?
 - How long should I wait before scaling back down?
 - Should I pre-warm capacity for known peaks?
 - How should I handle credentials for external event sources?
 - What is the cost of being wrong in either direction?
 
 Those are the questions that separate a demo from an operating model.
 
 A good technical article should leave readers with more than instructions. It should leave them with a sharper way to think about system behavior. That is what this demo tries to do.

 ## Final Takeaway
 
 KEDA is compelling because it makes autoscaling feel closer to application intent.
 
 Instead of asking Kubernetes to infer demand from resource pressure, you can teach it to react to signals your platform already understands: queue backlog, scheduled spikes, cloud messages, Kafka lag, or database activity.
 
 For this demo, the signals are basketball-content backlog in Redis and recap backlog in RabbitMQ.
 
 In a real platform, that backlog could represent orders, messages, videos, ETL tasks, alerts, or event streams.
 
 The principle stays the same:
 
 **scale based on the thing your users are actually waiting for.**
 
 If you want to publish this on Medium, the article is now strong enough to support screenshots from the live demo, a clean hero image, and a short call to action linking back to the repository. Those final touches will make it feel like a polished technical story rather than an internal draft.
