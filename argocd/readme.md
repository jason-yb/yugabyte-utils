# ArgoCD example using YugabyteDB Anywhere Operator

The YugabyteDB Anywhere Operator allows you to integrate YugabyteDB into a GitOps workflow, enabling declarative management of database deployments on Kubernetes clusters.

This example can be used with an ArgoCD app to deploy YugabyteDB Anywhere, with the operator enabled, and create an example universe via the operator.

## Prerequisites

- A running Kubernetes cluster (e.g., GKE, EKS, AKS)
- [Argo CD](https://argo-cd.readthedocs.io/en/stable/getting_started/) installed and configured
- Access to the GitHub repo: https://github.com/jason-yb/yugabyte-utils

## Steps

1. Set Up Argo CD: Install and configure Argo CD in your Kubernetes cluster.
2. Clone the Repository: Clone the jason-yb/yugabyte-utils repository.
3. Replace the secret with a secret obtain from Yugabyte 
3.Review and Update Manifests: Examine the provided manifests and configurations, updating to suit your specific deployment requirements.
4. Apply Configurations: Use Argo CD to apply the configurations, which will deploy and manage YugabyteDB according to the defined specifications.