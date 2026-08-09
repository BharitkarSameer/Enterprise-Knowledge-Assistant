# Payment Service Runbook

Internal operations guide for the `payments-api` service.
Use this document during incidents, deploys, and rollbacks.

## Overview

`payments-api` handles authorization, capture, and refund flows for checkout.

Owned by:

- Team: Payments Platform
- On-call: `#payments-oncall`
- Repo: `github.com/acme/payments-api`

## Prerequisites

Before making production changes, confirm the following:

1. You are on the VPN
2. You have `kubectl` access to the `prod-payments` namespace
3. Change ticket is approved in Jira

### Required tools

Install and verify:

```bash
kubectl version --client
helm version
curl -I https://payments.internal.acme.com/health
```

#### Local env tip

Copy `.env.example` to `.env` and set `PAYMENTS_API_KEY` before running smoke tests.

## Deploy

### Pre-deploy checklist

| Check | Owner | Status |
|-------|-------|--------|
| Migrations reviewed | Backend | Required |
| Feature flags set | Platform | Required |
| Dashboard green | On-call | Required |

### Deploy steps

1. Tag the release
2. Sync ArgoCD application
3. Verify pods are ready

```bash
git tag -a v2.14.0 -m "payments-api v2.14.0"
git push origin v2.14.0
kubectl -n prod-payments rollout status deploy/payments-api
```

### Post-deploy verification

Hit health and a canary charge:

```bash
curl -s https://payments.internal.acme.com/health | jq .
curl -s -X POST https://payments.internal.acme.com/v1/charges/canary \
  -H "Authorization: Bearer $PAYMENTS_API_KEY"
```

Expected health response:

```json
{
  "status": "ok",
  "version": "2.14.0",
  "db": "up"
}
```

## Rollback

Use this section if error rate exceeds 2% or p95 latency exceeds 800ms for 5 minutes.

### When to rollback

Rollback immediately if any of these are true:

- Payment success rate drops below 98%
- Pod crash loop is observed
- Downstream ledger rejects > 1% of writes

### Rollback procedure

| Step | Action | Command / note |
|------|--------|----------------|
| 1 | Stop new traffic | Scale canary to 0 |
| 2 | Revert deploy | Rollout undo |
| 3 | Confirm health | Check `/health` |
| 4 | Notify stakeholders | Post in `#payments-oncall` |

```bash
kubectl -n prod-payments scale deploy/payments-api-canary --replicas=0
kubectl -n prod-payments rollout undo deploy/payments-api
kubectl -n prod-payments rollout status deploy/payments-api
```

#### Known false positive

A single region blip in `us-east-1` can look like a payments outage. Check multi-region dashboards before rolling back globally.

## Escalation

If rollback does not restore service within 15 minutes:

- Page Payments Platform primary
- Join Zoom bridge from the incident channel
- Capture timeline in the incident doc

Contact matrix:

| Severity | Contact | Channel |
|----------|---------|---------|
| SEV-1 | Payments primary + Eng Manager | PagerDuty + Zoom |
| SEV-2 | Payments primary | `#payments-oncall` |
| SEV-3 | Team backlog | Jira |

## Appendix

### Common error codes

| Code | Meaning | Next action |
|------|---------|-------------|
| `PAY_TIMEOUT` | Gateway timeout | Check acquirer status page |
| `PAY_DUP` | Duplicate idempotency key | Safe to ignore / retry read |
| `PAY_AUTH` | Auth token invalid | Rotate service credentials |

### Useful links

- [Grafana dashboard](https://grafana.internal.acme.com/d/payments)
- [Runbook index](https://wiki.internal.acme.com/runbooks)
- [Incident template](https://wiki.internal.acme.com/incidents/template)
