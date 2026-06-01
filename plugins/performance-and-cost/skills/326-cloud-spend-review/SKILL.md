---
name: cloud-spend-review
description: Use when you need to review cloud spend for waste — rightsizing over-provisioned compute, finding idle and orphaned resources, storage tiering, data egress charges, reserved/spot/committed-use discounts, cost-allocation tagging, and cost-anomaly alerting.
---

# Cloud Spend Review

## Purpose

Find and remove cloud waste with evidence, and put guardrails in place so it does not return. This is read-and-recommend work: rightsizing over-provisioned compute against real utilization, deleting idle and orphaned resources (unattached disks, idle load balancers, stale snapshots, unused IPs), moving cold data to cheaper storage tiers, attacking data-egress charges, applying reserved/spot/committed-use discounts to steady baseload, enforcing cost-allocation tagging, and wiring cost-anomaly alerts. The output is a ranked savings list with the evidence behind each line and the safe action to capture it — never a blind "delete to save money."

## When to use

- The monthly cloud bill is rising and the largest line items have not been attributed to a service or team.
- Instances/databases were sized for peak or "to be safe" and run far below their provisioned CPU/memory.
- You suspect orphaned resources (disks with no instance, unattached IPs, old snapshots, idle load balancers).
- A surprising data-transfer/egress charge appears and the cross-region or internet path is unclear.
- Steady baseload runs entirely on on-demand pricing with no reserved/committed/spot coverage.
- Untagged spend makes it impossible to attribute cost to teams or environments.

## When not to use

- The workload is already efficiently sized and discount-covered, and the remaining spend is genuine working cost — there is no waste to cut.
- The "cost" is per-token LLM/API billing — use LLM API cost optimization instead.
- A one-time spike came from a known, finished batch job that has already stopped.

## Procedure

1. **Attribute the bill before cutting anything.** Pull cost grouped by service, region, account/project, and tag for the last 30–90 days. Rank the top line items; a few services usually dominate (the 80/20 rule holds for cloud bills). You cannot prioritize savings you have not attributed, and cutting the small lines first wastes effort.
2. **Rightsize against real utilization.** For compute and databases, compare provisioned vCPU/memory against actual p95 utilization over weeks. Persistently low utilization (e.g., p95 CPU under ~20–40%) is a rightsizing candidate — step down a size or move to autoscaling, not delete. Account for memory as well as CPU; a memory-bound workload may need its current size even at low CPU.
3. **Hunt idle and orphaned resources.** List resources with no attachment or no traffic: unattached block volumes, unassociated static IPs, idle/empty load balancers, stopped instances still billing for disks, and snapshots/AMIs older than the retention policy. These accrue silently because nobody owns a resource that nothing points at.
4. **Tier storage by access pattern.** Identify cold objects (not read in N days) and move them to infrequent-access/archive tiers via lifecycle rules. Check that frequently-read data is NOT in an archive tier where retrieval fees and latency would dominate — a wrong tier can cost more than the standard tier it replaced.
5. **Attack egress.** Find cross-region, cross-AZ, and internet egress charges. Co-locate chatty services, put a CDN in front of repeated public downloads, and use private/VPC endpoints to keep traffic off the metered internet path. Egress is metered per GB and rarely appears as a single obvious line, so it hides in plain sight.
6. **Cover baseload with commitments and spot.** Quantify the steady 24/7 floor and cover it with reserved instances / committed-use / savings plans; run fault-tolerant, interruptible work (batch, CI, stateless workers) on spot/preemptible. Do not over-commit beyond the proven floor, because an unused commitment is locked-in waste, not a discount.
7. **Schedule non-production environments.** Dev, staging, and test environments rarely need to run 24/7. Confirm they auto-stop outside business hours; an always-on non-prod fleet is one of the most common and easiest-to-fix sources of waste.
8. **Enforce tagging and wire anomaly alerts.** Require cost-allocation tags (team, env, service) and report untagged spend. Turn on the provider's cost-anomaly detection plus a budget alert so the next regression pages someone instead of surfacing in next month's invoice — guardrails stop waste from recurring after this review ends.

## Concrete checks

- [ ] Spend is attributed by service, region, account/project, and tag; the top line items are ranked.
- [ ] Compute/database provisioned size is compared against weeks of real p95 utilization (not a single reading).
- [ ] Unattached volumes, unassociated IPs, idle load balancers, and stale snapshots/images are enumerated.
- [ ] Stopped instances are checked for disks/IPs that still bill while stopped.
- [ ] Storage lifecycle rules move cold data to cheaper tiers; hot data is not stranded in archive.
- [ ] Cross-region/cross-AZ and internet egress charges are identified and attributed to a path.
- [ ] Steady baseload coverage by reserved/committed/savings plans is quantified vs. on-demand.
- [ ] Interruptible workloads run on spot/preemptible where safe.
- [ ] A mandatory tagging policy exists and untagged spend is measured.
- [ ] Non-production environments are scheduled to stop outside working hours, not left always-on.
- [ ] Log and metrics retention windows match what is actually queried, not an open-ended default.
- [ ] Cost-anomaly detection and a budget alert are enabled.

## Commands or Templates

```bash
# --- AWS: spend grouped by service (last 30 days), top drivers first ---
aws ce get-cost-and-usage \
  --time-period Start=$(date -v-30d +%F),End=$(date +%F) \
  --granularity MONTHLY --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[].Groups[].{svc:Keys[0],usd:Metrics.UnblendedCost.Amount}'

# Orphaned EBS volumes (status 'available' = attached to nothing)
aws ec2 describe-volumes --filters Name=status,Values=available \
  --query 'Volumes[].{id:VolumeId,gib:Size,az:AvailabilityZone,created:CreateTime}'

# Unassociated Elastic IPs (billed when not attached)
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].{ip:PublicIp,alloc:AllocationId}'

# Snapshots older than retention (older than ~90 days here)
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[?StartTime<='$(date -v-90d +%F)'].{id:SnapshotId,gib:VolumeSize,when:StartTime}"

# Untagged running instances (no 'team' tag = unattributed spend)
aws ec2 describe-instances --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[?!not_null(Tags[?Key==`team`])].InstanceId'
```

```bash
# --- GCP: spend by service and recommender (rightsizing) ---
gcloud billing accounts list
# Idle/rightsizing suggestions from the recommender API
gcloud recommender recommendations list \
  --recommender=google.compute.instance.MachineTypeRecommender \
  --location=<zone> --format='table(description, primaryImpact.costProjection.cost)'
# Unattached persistent disks
gcloud compute disks list --filter="-users:*" \
  --format='table(name, sizeGb, zone, creationTimestamp)'
```

```bash
# --- Rightsizing evidence: p95 CPU over 14 days (AWS CloudWatch) ---
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=<id> \
  --start-time $(date -v-14d +%FT%T) --end-time $(date +%FT%T) \
  --period 3600 --extended-statistics p95 \
  --query 'Datapoints[].ExtendedStatistics.p95' | sort -rn | head
```

```json
// S3 lifecycle rule: tier cold objects down, then expire — recommend, do not auto-apply.
{
  "Rules": [{
    "ID": "tier-and-expire-logs",
    "Filter": { "Prefix": "logs/" },
    "Status": "Enabled",
    "Transitions": [
      { "Days": 30,  "StorageClass": "STANDARD_IA" },
      { "Days": 90,  "StorageClass": "GLACIER" }
    ],
    "Expiration": { "Days": 365 }
  }]
}
```

```bash
# Idle load balancers: ALBs with zero processed requests over the window are waste.
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB \
  --metric-name RequestCount --statistics Sum --period 86400 \
  --dimensions Name=LoadBalancer,Value=<lb-arn-suffix> \
  --start-time $(date -v-14d +%FT%T) --end-time $(date +%FT%T) \
  --query 'sum(Datapoints[].Sum) == `0` && `IDLE` || `IN_USE`'
```

## Common issues & anti-patterns

- **Deleting before attributing.** Removing resources to "save money" without confirming they are idle risks an outage; gather evidence (no attachment, no traffic, age) first.
- **Rightsizing on one data point.** A single low-CPU reading is meaningless; size to weeks of p95, accounting for batch/peak windows.
- **Over-committing reservations.** Buying reserved/committed capacity above the proven 24/7 floor locks in spend you do not use; cover only the baseload.
- **Putting hot data in archive.** Archive tiers have retrieval fees and latency; moving frequently-read data there can cost more than it saves.
- **Ignoring egress.** Cross-region/AZ and internet transfer is a top hidden cost; chatty cross-region calls and un-CDN'd downloads quietly dominate the bill.
- **Forgotten stopped instances.** A stopped VM still bills for its attached disks and IPs; "stopped" is not "free."
- **No tags, no accountability.** Untagged spend cannot be attributed, so waste has no owner and recurs.
- **Always-on non-production environments.** Dev/staging fleets left running 24/7 burn money outside working hours for no benefit; schedule them to stop.
- **Over-provisioned logging/metrics retention.** Keeping verbose logs and high-resolution metrics far longer than anyone queries them is a silent, compounding storage cost.
- **Premium support/managed tiers chosen by default.** Paying for the highest service tier on workloads that do not need it (e.g., multi-AZ on a throwaway environment) inflates the bill without value.
- **No anomaly alert.** Without anomaly detection and a budget alert, the next runaway resource is discovered on the invoice.

## Required output

Produce a report containing:
1. **Spend attribution** — top line items by service/region/account/tag, with each line's share of the bill.
2. **Rightsizing table** — resource, provisioned size, p95 utilization, recommended size, and estimated monthly saving.
3. **Idle/orphaned list** — each unattached/idle/stale resource with evidence (no attachment, no traffic, age) and the saving.
4. **Storage & egress** — cold-data tiering opportunities and the egress paths driving transfer cost, each with a fix.
5. **Commitment plan** — quantified baseload and recommended reserved/committed/spot coverage (and what NOT to commit).
6. **Governance** — tagging gaps and the anomaly/budget alert status.
7. **Ranked savings + next safe action** — total estimated monthly saving, prioritized, with the safest first step (usually deleting evidenced orphans or tiering cold storage).

## Safety

- This is a read-and-recommend review: do not delete, resize, or terminate any resource; produce evidenced recommendations and let an owner act with approval.
- A resource being idle now does not prove it is safe to remove (DR standby, seasonal, scheduled job) — flag and confirm ownership before recommending deletion.
- Never print account IDs, access keys, or credentials in the report; reference accounts/projects by name or alias and redact identifiers.
- Use read-only cost/inventory APIs; do not run write/delete CLI calls during the review.
- Verify a snapshot/AMI is not the only backup of important data before recommending its deletion.
- Treat reserved/committed purchases as a finance decision; recommend the coverage, but do not buy commitments.
