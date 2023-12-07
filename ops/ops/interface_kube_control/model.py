from pydantic import Field, AnyHttpUrl, BaseModel, Json
from typing import List, Dict, Optional
import re


class _ValidatedStr:
    def __init__(self, value, *groups) -> None:
        self._str = value
        self.groups = groups

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        m = cls.REGEX.match(v)
        if not m:
            raise ValueError("invalid format")
        return cls(v, *m.groups())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._str},*{self.groups})"

    @property
    def key(self) -> str:
        return self.groups[0]

    @property
    def value(self) -> Optional[str]:
        return self.groups[1]


class Label(_ValidatedStr):
    REGEX = re.compile(r"^([\w\d\-\.\/]+)=([\w\d\-\.]*)$")


class Taint(_ValidatedStr):
    REGEX = re.compile(r"^([\w\d\-\.\/]+)(?:=([\w\d\-\.]*))?:([\w\d\-\.]+)$")

    @property
    def effect(self) -> str:
        return self.groups[2]


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
    sdn_ip: Optional[str] = Field(default=None, alias="sdn-ip")
    registry_location: str = Field(alias="registry-location")
    taints: Optional[Json[List[Taint]]] = Field(alias="taints")
    labels: Optional[Json[List[Label]]] = Field(alias="labels")
