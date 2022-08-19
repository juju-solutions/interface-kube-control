from pydantic import Field, AnyHttpUrl, BaseModel, Json
from typing import List, Dict, Optional


class Creds(BaseModel):
    client_token: str
    kubelet_token: str
    proxy_token: str
    scope: str


class Data(BaseModel):
    api_endpoints: Json[List[AnyHttpUrl]] = Field(alias="api-endpoints")
    cluster_tag: str = Field(alias="cluster-tag")
    cohort_keys: Optional[Json[Dict[str, str]]] = Field(alias="cohort-keys")
    creds: Json[Dict[str, Creds]] = Field(alias="creds")
    default_cni: Json[str] = Field(alias="default-cni")
    domain: str = Field(alias="domain")
    enable_kube_dns: bool = Field(alias="enable-kube-dns")
    has_xcp: Json[bool] = Field(alias="has-xcp")
    port: Json[int] = Field(alias="port")
    sdn_ip: str = Field(alias="sdn-ip")
    registry_location: str = Field(alias="registry-location")
    taints: Optional[List[str]] = Field(alias="taints")
    labels: Optional[List[str]] = Field(alias="labels")
