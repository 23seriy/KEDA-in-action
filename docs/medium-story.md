# KEDA in Action: Event-Driven Autoscaling on Your Laptop

Most Kubernetes autoscaling demos start with CPU usage. That makes sense because CPU is easy to measure, easy to explain, and already built into the ecosystem. But CPU is often the wrong signal.

If your platform processes jobs from a queue, the real question is not whether pods are busy right now. The real question is whether work is piling up.

That is where KEDA becomes interesting.

This project tells a simple story: imagine a basketball media pipeline for an NBA fan app. During a quiet afternoon, almost nothing is happening. Then tip-off arrives, a superstar drops 15 in the first quarter, and suddenly everyone wants highlight clips, stat cards, and game recap assets at once. The API is lightweight. It receives a request and pushes a message into Redis. The expensive part happens later, inside worker pods. When there are no games, you want zero workers. When a burst of game-night requests arrives, you want Kubernetes to wake workers up quickly and add more as backlog grows.

That is a much more natural scaling model than “CPU above 70% means maybe scale out.”

## The Architecture

The demo has only three moving parts.

- A **producer API** that submits basketball content jobs into a Redis list.
- A **worker deployment** that continuously pulls jobs and simulates processing.
- A **KEDA ScaledObject** that watches queue depth and adjusts worker replicas.

This makes the feedback loop easy to understand:

1. Users create work.
2. Work becomes queue depth.
3. Queue depth becomes replicas.
4. Replicas drain the queue.
5. When the queue is empty, workers can return to zero.

That last part is the magic. Traditional HPAs do not really shine when the best number of pods is sometimes zero. KEDA does.

## Why This Feels Different From CPU-Based Autoscaling

CPU-based autoscaling is indirect. It guesses demand by observing resource pressure.

KEDA lets you scale on a first-class business event.

For a queue consumer, queue length is usually a better signal because it answers the question you actually care about: **Are fans waiting?**

If ten thousand jobs arrive in one minute, you do not need to wait for average CPU to slowly drift upward before reacting. You already know demand has spiked because the backlog is visible immediately.

## Scenario 1: Default Queue Scaling

The first ScaledObject uses a Redis list trigger with a threshold of 5. That means KEDA becomes more eager to add pods once backlog crosses a modest level.

This setup is a good default when:
 
 - fan wait time matters
 - highlight and stat jobs are moderately heavy
 - you want a responsive demo that visibly scales on command
 
 From the UI or API, submit 10 or 50 jobs. Then watch the worker deployment in another terminal. The interesting thing is not only that pods scale out. It is that the queue itself is the reason. In basketball terms, demand is driven by game moments, not by generic infrastructure noise.

## Scenario 2: Conservative Scaling

Next, increase the threshold to 20.

 This changes the tone of the system. Now it tolerates more backlog before scaling aggressively. That can be acceptable if jobs are short, infrastructure cost matters, or queue delay is not very noticeable to fans.

This is an important KEDA lesson: scaling is not just “on or off.” It is policy. The threshold encodes what level of waiting your platform considers acceptable.

## Scenario 3: Faster Polling, Faster Recovery

Polling interval and cooldown period look like boring tuning knobs until you experience them.

A shorter polling interval makes the system react faster to a burst. A shorter cooldown also lets it shed capacity sooner once demand disappears. That sounds perfect, but there is a tradeoff: very aggressive settings can create more noise and scaling churn.

KEDA gives you the freedom to tune that tradeoff around workload behavior rather than around generic CPU assumptions.

## Scenario 4: Cron + Event Triggers Together

One of my favorite KEDA ideas is that event-driven and time-based scaling can coexist.

Suppose your team already knows that every weekday at 8 AM a large ingestion batch starts. You can pre-warm two workers before the queue grows. Then, if the backlog becomes larger than expected, the Redis scaler adds more.

That hybrid model feels realistic. Many systems have both predictable peaks and unpredictable spikes.

## What This Project Teaches Beyond the Happy Path

This repository is intentionally small, but it encourages the right questions:

- What is the most truthful signal for my workload?
- How quickly should I react to demand?
- How long should I wait before scaling back down?
- Should I keep a warm baseline, or let it truly scale to zero?
- Where is the line between efficiency and responsiveness?

Those are the operational questions that matter in production.

## Final Takeaway

KEDA is compelling because it makes autoscaling feel closer to application intent.

Instead of asking Kubernetes to infer demand from resource pressure, you can teach it to react to the events your system already understands: queue backlog, scheduled spikes, cloud messages, Kafka lag, database activity, and more.

That is why KEDA feels like a natural next step after learning the basics of Kubernetes scaling.

It is not just about scaling pods.

It is about scaling based on the thing your users are actually waiting for.
