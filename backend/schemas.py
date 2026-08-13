"""Pydantic request and response schemas for FastAPI Sentra API endpoints."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthorityRequestSchema(BaseModel):
    agentId: str = Field(..., example="ops_agent")
    tool: str = Field(..., example="deploy_service")
    action: str = Field(..., example="deploy")
    resource: str = Field(..., example="prod_k8s_cluster")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requestedAt: str = Field(..., example="2026-08-13T22:00:00Z")
    nonce: str = Field(..., example="nonce-12345")
    policyVersion: str = Field(default="v1.0.0-sentra-kernel")
    promptContext: Optional[str] = None


class ScenarioRunRequest(BaseModel):
    scenario: str = Field(..., example="valid_action")


class VerifyAndExecuteRequest(BaseModel):
    capabilityId: str
    request: AuthorityRequestSchema
    requestHash: str


class CapabilityOut(BaseModel):
    id: str
    requestHash: str
    scope: Dict[str, Any]
    signature: str
    expiresAt: datetime
    status: str
    nonce: str


class DecisionOut(BaseModel):
    decision: str
    reasonCode: str
    explanation: str
    requestHash: str
    canonicalRequest: str
    policyVersion: str
    capability: Optional[Dict[str, Any]] = None


class GatewayExecutionOut(BaseModel):
    status: str
    resourceId: str
    newState: Dict[str, Any]
    capabilityId: str
    consumedAt: str
    proofEventHash: str


class AuthorityEventOut(BaseModel):
    id: str
    sequence: int
    request_hash: str
    decision: str
    reason_code: str
    previous_hash: str
    event_hash: str
    payload: Dict[str, Any]
    created_at: datetime


class ResourceOut(BaseModel):
    id: str
    label: str
    state: Dict[str, Any]
    updated_at: datetime


class DashboardOut(BaseModel):
    resources: List[ResourceOut]
    recentEvents: List[AuthorityEventOut]
    capabilities: List[CapabilityOut]
    proofChainStatus: Dict[str, Any]
    totalVerdicts: int
    allowedCount: int
    deniedCount: int
