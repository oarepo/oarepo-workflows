# OARepo Workflows

Workflow management for [Invenio](https://inveniosoftware.org/) records.

## Overview

This package enables state-based workflow management for Invenio records with:

- State-based record lifecycle management with timestamps
- Configurable permission policies per workflow state
- Request-based state transitions with approval workflows
- Auto-approval and escalation mechanisms
- Model presets for automatic integration with oarepo-model
- Multiple recipient support for requests

## Installation

```bash
pip install oarepo-workflows
```

### Requirements

- Python 3.13+
- Invenio 14.x (RDM)
- oarepo-runtime >= 2.0.0

## Key Features

### 1. Workflow Definition and Management

**Source:** [`oarepo_workflows/base.py`](oarepo_workflows/base.py), [`oarepo_workflows/ext.py`](oarepo_workflows/ext.py)

Define workflows with state-based permissions and request policies:

```python
from oarepo_workflows import Workflow
from flask_babel import lazy_gettext as _

WORKFLOWS = {
    "default": Workflow(
        code="default",
        label=_("Default Workflow"),
        permission_policy_cls=DefaultWorkflowPermissions,
        request_policy_cls=DefaultWorkflowRequests,
    )
}
```

Access workflows through the extension:

```python
from oarepo_workflows import current_oarepo_workflows

# Get workflow by code
workflow = current_oarepo_workflows.workflow_by_code["default"]

# Get workflow from record
workflow = current_oarepo_workflows.get_workflow(record)

# List all workflows
workflows = current_oarepo_workflows.record_workflows
```

### 2. Record System Fields

**Source:** [`oarepo_workflows/records/systemfields/`](oarepo_workflows/records/systemfields/)

#### State Field

Tracks the current state of a record with automatic timestamp updates:

```python
from oarepo_workflows.records.systemfields import (
    RecordStateField,
    RecordStateTimestampField,
)

class MyRecord(Record):
    state = RecordStateField(initial="draft")
    state_timestamp = RecordStateTimestampField()
```

Set state programmatically:

```python
from oarepo_workflows import current_oarepo_workflows

# Change state with automatic notification
current_oarepo_workflows.set_state(
    identity,
    record,
    "published",
    commit=True,
    notify_later=True
)
```

#### Workflow Field

Links parent records to their workflow definition:

```python
from oarepo_workflows.records.systemfields import WorkflowField

class MyParentRecord(ParentRecord):
    workflow = WorkflowField()
```

### 3. Permission Management

**Source:** [`oarepo_workflows/services/permissions/`](oarepo_workflows/services/permissions/)

#### Workflow Permission Policy

Define state-based permissions for record operations:

```python
from oarepo_workflows.services.permissions import (
    DefaultWorkflowPermissions,
    IfInState,
)
from invenio_rdm_records.services.generators import RecordOwners
from invenio_records_permissions.generators import AuthenticatedUser

class MyWorkflowPermissions(DefaultWorkflowPermissions):
    can_create = [AuthenticatedUser()]
    
    can_read = [
        IfInState("draft", [RecordOwners()]),
        IfInState("published", [AuthenticatedUser()]),
    ]
    
    can_update = [
        IfInState("draft", [RecordOwners()]),
    ]
    
    can_delete = [
        IfInState("draft", [RecordOwners()]),
    ]
```

**Key permission generators:**

- `IfInState(state, then_generators, else_generators)` - Conditional permissions based on record state
- `FromRecordWorkflow(action)` - Delegate permission check to workflow policy
- `SameAs(permission_name)` - Reuse permissions from another action

#### Record Permission Policy

Use `WorkflowRecordPermissionPolicy` on `RecordServiceConfig` to delegate all permissions to workflows:

```python
from oarepo_workflows.services.permissions import (
    WorkflowRecordPermissionPolicy,
)

class MyServiceConfig(RecordServiceConfig):
    permission_policy_cls = WorkflowRecordPermissionPolicy
```

### 4. Request-Based Workflows

**Source:** [`oarepo_workflows/requests/`](oarepo_workflows/requests/)

#### Request Definition

Define requests that move records through workflow states:

```python
from oarepo_workflows import (
    WorkflowRequest,
    WorkflowRequestPolicy,
    WorkflowTransitions,
    IfInState,
)
from invenio_rdm_records.services.generators import RecordOwners

class MyWorkflowRequests(WorkflowRequestPolicy):
    publish_request = WorkflowRequest(
        requesters=[
            IfInState("draft", [RecordOwners()])
        ],
        recipients=[CommunityRole("curator")],
        transitions=WorkflowTransitions(
            submitted="submitted",
            accepted="published",
            declined="draft"
        )
    )
```

**Request configuration:**

- `requesters` - Generators defining who can create the request
- `recipients` - Generators defining who can approve the request
- `transitions` - State changes for submitted/accepted/declined/cancelled
- `events` - Additional events that can be submitted with the request
- `escalations` - Auto-escalation if not resolved in time

#### Auto-Approval

Automatically approve requests when submitted:

```python
from oarepo_workflows import AutoApprove

class MyWorkflowRequests(WorkflowRequestPolicy):
    edit_request = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[AutoApprove()],
    )
```

#### Request Escalation

Escalate unresolved requests to higher authority:

```python
from datetime import timedelta
from oarepo_workflows import WorkflowRequestEscalation

class MyWorkflowRequests(WorkflowRequestPolicy):
    delete_request = WorkflowRequest(
        requesters=[IfInState("published", [RecordOwners()])],
        recipients=[CommunityRole("curator")],
        transitions=WorkflowTransitions(
            submitted="deleting",
            accepted="deleted",
            declined="published"
        ),
        escalations=[
            WorkflowRequestEscalation(
                after=timedelta(days=14),
                recipients=[UserWithRole("administrator")]
            )
        ]
    )
```

#### Request Events

Define custom events that can be submitted on requests:

```python
from oarepo_workflows.requests import WorkflowEvent

class MyWorkflowRequests(WorkflowRequestPolicy):
    review_request = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[CommunityRole("reviewer")],
        events={
            "request_changes": WorkflowEvent(
                submitters=[CommunityRole("reviewer")]
            )
        }
    )
```

### 5. Request Permissions

**Source:** [`oarepo_workflows/requests/permissions.py`](oarepo_workflows/requests/permissions.py)

The package provides `CreatorsFromWorkflowRequestsPermissionPolicy` which automatically extracts request creators from workflow definitions:

```python
# In invenio.cfg
from oarepo_workflows.requests.permissions import (
    CreatorsFromWorkflowRequestsPermissionPolicy,
)

REQUESTS_PERMISSION_POLICY = CreatorsFromWorkflowRequestsPermissionPolicy
```

This policy:

- Checks workflow request definitions for `can_create` permissions
- Supports event-specific permissions (e.g., `can_<request>_<event>_create`)
- Allows any user to search requests (but filters results by actual permissions)

### 6. Service Components

**Source:** [`oarepo_workflows/services/components/`](oarepo_workflows/services/components/)

#### Workflow Component

Ensures workflow is set when creating records:

```python
from oarepo_workflows.services.components import WorkflowComponent

class MyServiceConfig(RecordServiceConfig):
    components = [
        WorkflowComponent,
        # ... other components
    ]
```

The component:

- Validates workflow presence in input data
- Sets workflow on parent record during creation
- Runs before metadata component to ensure workflow-based permissions apply

### 7. Model Presets

**Source:** [`oarepo_workflows/model/presets/`](oarepo_workflows/model/presets/)

Automatic integration with `oarepo-model` code generator:

#### Record Presets

- `WorkflowsParentRecordPreset` - Adds `WorkflowField` to parent records
- `WorkflowsDraftPreset` - Adds `RecordStateField` and `RecordStateTimestampField` to drafts
- `WorkflowsRecordPreset` - Adds state fields to published records
- `WorkflowsParentRecordMetadataPreset` - Adds workflow column to parent metadata table
- `WorkflowsMappingPreset` - Adds OpenSearch mappings for state and workflow fields

#### Service Presets

- `WorkflowsServiceConfigPreset` - Adds `WorkflowComponent` to service components
- `WorkflowsPermissionPolicyPreset` - Sets `WorkflowRecordPermissionPolicy` on service config
- `WorkflowsParentRecordSchemaPreset` - Adds workflow field to parent schema
- `WorkflowsRecordSchemaPreset` - Adds state fields to record schema

### 8. State Change Notifications

**Source:** [`oarepo_workflows/services/uow.py`](oarepo_workflows/services/uow.py)

Register custom handlers for state changes via entry points:

```python
# In your package
def my_state_change_handler(
    identity,
    record,
    previous_state,
    new_state,
    *args,
    uow=None,
    **kwargs
):
    # Handle state change
    pass

# In pyproject.toml
[project.entry-points."oarepo_workflows.state_changed_notifiers"]
my_handler = "my_package.handlers:my_state_change_handler"
```

### 9. Multiple Recipients

**Source:** [`oarepo_workflows/services/multiple_entities/`](oarepo_workflows/services/multiple_entities/)

Support for requests with multiple recipients:

```python
from oarepo_workflows import WorkflowRequest

class MyWorkflowRequests(WorkflowRequestPolicy):
    review_request = WorkflowRequest(
        requesters=[RecordOwners()],
        recipients=[
            CommunityRole("reviewer"),
            CommunityRole("curator")
        ]
    )
```

The first recipient becomes the primary recipient. Multiple recipients are tracked via the `multiple` entity resolver.

## Configuration

### Basic Configuration

In `invenio.cfg`:

```python
from oarepo_workflows import Workflow
from my_workflows.permissions import DefaultPermissions
from my_workflows.requests import DefaultRequests

WORKFLOWS = {
    "default": Workflow(
        code="default",
        label="Default Workflow",
        permission_policy_cls=DefaultPermissions,
        request_policy_cls=DefaultRequests,
    )
}
```

### Community Roles

Define roles used in workflow permissions:

```python
from invenio_i18n import lazy_gettext as _

COMMUNITIES_ROLES = [
    dict(
        name="curator",
        title=_("Curator"),
        description=_("Curator of the community")
    ),
    dict(
        name="reviewer",
        title=_("Reviewer"),
        description=_("Reviewer of submissions")
    ),
]
```

### Default Workflow Events

Define events available to all workflows:

```python
from oarepo_workflows.requests import WorkflowEvent

DEFAULT_WORKFLOW_EVENTS = {
    "comment": WorkflowEvent(
        submitters=[Creator(), Receiver()]
    )
}
```

## Development

### Setup

```bash
git clone https://github.com/oarepo/oarepo-workflows.git
cd oarepo-workflows
./run.sh venv
```

### Running Tests

```bash
./run.sh test
```

## Entry Points

The package registers several Invenio entry points:

```python
[project.entry-points."invenio_base.apps"]
oarepo_workflows = "oarepo_workflows.ext:OARepoWorkflows"

[project.entry-points."invenio_base.api_apps"]
oarepo_workflows = "oarepo_workflows.ext:OARepoWorkflows"

[project.entry-points."invenio_requests.entity_resolvers"]
auto_approve = "oarepo_workflows.resolvers.auto_approve:AutoApproveResolver"
multiple = "oarepo_workflows.resolvers.multiple_entities:MultipleEntitiesResolver"

[project.entry-points."invenio_base.finalize_app"]
oarepo_workflows = "oarepo_workflows.ext:finalize_app"

[project.entry-points."invenio_base.api_finalize_app"]
oarepo_workflows = "oarepo_workflows.ext:finalize_app"

[project.entry-points."invenio_config.module"]
oarepo_workflows = "oarepo_workflows.initial_config"
```

## License

Copyright (c) 2024-2025 CESNET z.s.p.o.

OARepo Workflows is free software; you can redistribute it and/or modify it under the terms of the MIT License. See [LICENSE](LICENSE) file for more details.

## Links

- Documentation: <https://github.com/oarepo/oarepo-workflows>
- PyPI: <https://pypi.org/project/oarepo-workflows/>
- Issues: <https://github.com/oarepo/oarepo-workflows/issues>
- OARepo Project: <https://github.com/oarepo>

## Acknowledgments

This project builds upon [Invenio Framework](https://inveniosoftware.org/) and is developed as part of the OARepo ecosystem.
