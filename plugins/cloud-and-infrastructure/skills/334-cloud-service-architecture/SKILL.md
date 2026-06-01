---
name: cloud-service-architecture
description: Use when you need to choose or review cloud architecture decisions — managed vs self-hosted services, multi-AZ high availability, scaling strategy, VPC/subnet/network design, least-privilege service roles, and cost-aware tradeoffs.
---

# Cloud Service Architecture

## Purpose

Guide and review cloud architecture decisions across providers — choosing managed services over self-hosted where it lowers operational risk, designing for multi-AZ availability, sizing and autoscaling, laying out VPC/subnet/routing/egress, attaching least-privilege roles to each service, and keeping the design cost-aware. The goal is an architecture that meets the stated availability and scale targets at a justified cost, with explicit tradeoffs documented so a human owner can approve it before anything is provisioned. Ground every recommendation in the project's actual requirements and existing IaC, not generic best-practice lists.

## When to use

- A new system or major component needs a cloud topology (compute, data store, queue, cache, networking).
- A team is deciding managed vs self-hosted (e.g., managed Postgres vs running it on VMs).
- An availability or scaling target changed (single-AZ to multi-AZ, fixed to autoscaled).
- VPC/subnet/security-group/egress design is being created or reworked.
- A cost review flags an over-provisioned or single-points-of-failure design.
- You are reviewing an architecture diagram or IaC for HA, scaling, and least-privilege gaps.

## When not to use

- The change is a single Terraform resource tweak — use the Terraform IaC review skill.
- The decision is purely application-level (framework, library) with no infrastructure impact.
- A formal Architecture Decision Record is the deliverable — use the ADR generator and feed it this analysis.

## Procedure

### 1. Capture requirements and constraints

```bash
# Find stated NFRs, SLOs, and existing infra in the repo
grep -rniE "availability|uptime|SLA|SLO|RTO|RPO|latency|throughput|budget|cost" docs/ README* 2>/dev/null | head -30
# Inventory current cloud resources declared in IaC
grep -rnE "resource\s+\"(aws|google|azurerm)_" . --include="*.tf" | sed -E 's/.*"(aws|google|azurerm)_([a-z_]+)".*/\1_\2/' | sort | uniq -c
```

Record: availability target, expected load and growth, data durability needs (RPO/RTO), latency budget, compliance/data-residency, and cost ceiling.

### 2. Decide managed vs self-hosted per component

For each stateful or operationally heavy component, compare a managed service against self-hosting on the axes: operational burden, failover/backup built in, scaling model, lock-in, and total cost. Prefer managed unless a hard constraint (cost at scale, residency, custom extensions) justifies self-hosting.

### 3. Design for availability (multi-AZ)

```bash
# Are subnets spread across multiple AZs? Single-AZ data tiers are a SPOF.
grep -rn "availability_zone\|multi_az\|zone" . --include="*.tf"
# Load balancer + multiple targets across AZs?
grep -rn "lb\|load_balancer\|target_group\|autoscaling_group" . --include="*.tf"
```

### 4. Design scaling

Choose horizontal autoscaling for stateless tiers (target CPU/RPS), managed read replicas / connection pooling for data tiers, and queues to absorb spikes. Define min/max bounds and a scale-in cooldown.

### 5. Design the network

```bash
# Public vs private subnet placement — data tiers belong in private subnets
grep -rn "map_public_ip_on_launch\|public_subnet\|private_subnet\|nat_gateway\|igw\|internet_gateway" . --include="*.tf"
# Egress controls and security-group scope
grep -rn "0\.0\.0\.0/0\|cidr_blocks\|egress\|ingress" . --include="*.tf"
```

### 6. Attach least-privilege roles and estimate cost

```bash
# Each service should assume a scoped role, not a shared admin identity
grep -rn "iam_role\|service_account\|managed_identity\|assume_role" . --include="*.tf"
# Cost estimate from a plan (read-only) if Infracost is available
infracost breakdown --path . 2>/dev/null || echo "infracost not installed — estimate manually"
```

## Concrete checks

- [ ] Each component has an explicit managed-vs-self-hosted decision with a one-line rationale.
- [ ] Stateful tiers (DB, cache, queue) are multi-AZ or have a documented single-AZ acceptance.
- [ ] Compute is fronted by a load balancer with targets in at least two AZs.
- [ ] Stateless tiers autoscale with defined min/max and a scale-in policy.
- [ ] Data tiers have backups/snapshots and a stated RPO/RTO.
- [ ] Databases and internal services live in private subnets, not public ones.
- [ ] Egress to the internet is via NAT/egress gateway, not public IPs on every node.
- [ ] Security groups reference other groups/CIDRs narrowly; no `0.0.0.0/0` to data ports.
- [ ] Every service assumes a scoped IAM role/service account, not a shared admin credential.
- [ ] A cost estimate exists and is compared against the budget ceiling.
- [ ] Single points of failure are enumerated and either removed or explicitly accepted.
- [ ] Region/AZ choice respects any data-residency requirement.

## Commands or Templates

```hcl
# Multi-AZ subnets + managed DB with failover — review target
data "aws_availability_zones" "available" { state = "available" }

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 4, count.index)
  # no map_public_ip_on_launch -> private
}

resource "aws_db_instance" "primary" {
  engine            = "postgres"
  multi_az          = true          # synchronous standby in another AZ
  storage_encrypted = true
  backup_retention_period = 7       # supports point-in-time recovery (RPO)
  # credentials come from a secret manager, never inline
}
```

```hcl
# Stateless tier: autoscaling behind a load balancer
resource "aws_autoscaling_group" "web" {
  min_size            = 2
  max_size            = 10
  vpc_zone_identifier = aws_subnet.private[*].id   # spread across AZs
  target_group_arns   = [aws_lb_target_group.web.arn]
}
```

```bash
# Read-only cost + plan review (no provisioning)
terraform plan -out=tfplan
infracost breakdown --path .          # monthly cost estimate for human review
```

## Common issues & anti-patterns

- Single-AZ database or cache treated as production-grade — one AZ outage takes the system down.
- Self-hosting stateful services on VMs without a real backup/failover plan "to save money".
- Data tiers in public subnets with public IPs — directly internet-reachable.
- Security groups opening DB ports to `0.0.0.0/0`.
- One shared admin IAM credential reused by every service (no blast-radius containment).
- Over-provisioned always-on instances where autoscaling or serverless would fit the load profile.
- No cost estimate before provisioning — budget surprises after the fact.
- Choosing the most managed/expensive option everywhere without weighing cost at scale.

## Required output

Produce a structured report with:
1. **Requirements** — availability target, load/growth, RPO/RTO, latency, budget, residency.
2. **Component decisions** — managed vs self-hosted per component with rationale.
3. **Availability** — AZ spread, failover, backups; enumerated single points of failure.
4. **Scaling** — autoscaling strategy and min/max bounds per tier.
5. **Network** — VPC/subnet layout, public/private placement, egress, security-group scope.
6. **Identity** — per-service role/least-privilege plan.
7. **Cost** — estimate vs budget; the biggest cost drivers and any over-provisioning.
8. **Tradeoffs & next safe action** — key tradeoffs and the decision a human should approve first.

## Safety

- This is a design and review skill. NEVER provision, modify, or delete cloud resources (`terraform apply`, `aws/gcloud/az create|delete`, console changes) without explicit human approval — produce the design and a `plan`/estimate for review.
- Only read-only inspection (`describe`/`list`/`plan`/`infracost breakdown`) is safe to run unattended.
- Never embed real credentials, account IDs, or secrets in diagrams or IaC; reference a secret manager.
- Flag, do not silently accept, any single point of failure or `0.0.0.0/0` exposure — require a human decision.
- Do not recommend disabling encryption, backups, or logging to cut cost without explicit owner sign-off.
- Cost estimates are advisory; confirm against the provider's pricing before committing budget.
