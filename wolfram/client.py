from __future__ import annotations

from json import JSONDecodeError
from urllib.parse import urlencode
from typing import TYPE_CHECKING, Dict, Literal, Optional, Sequence, Tuple, Union, overload

from wolfram.api import API, FullResultsAPI, SimpleAPI, ShortAPI, SpokenAPI, ConversationalAPI
from wolfram.exceptions import ParameterConflict

if TYPE_CHECKING:
  from aiohttp import ClientResponse
  from requests import Response

  from wolfram.models import FullResults, ConversationalResults, SimpleImage
  from wolfram.params import Bool, LatLong, Units

import aiohttp
import requests

class ClientBase:
  """The base class of Clients"""
  BASE_URL = "https://api.wolframalpha.com/"

  API_VERSION = {
    1: "v1/",
    2: "v2/"
  }

  def __init__(self, appid: str):
    self._appid = appid

  @property
  def appid(self) -> str:
    """The App ID in use by the client"""
    return self._appid



class Client(ClientBase):
  """Client to interact with the APIs"""

  def query(self, api: API, url: Optional[str] = None, **params):
    if not issubclass(api, API):
      raise TypeError("api must be `API` type")


    if api.VERSION not in self.API_VERSION.keys():
      raise ValueError(f"Unknown API version '{request.version}'.")

    api_version = self.API_VERSION[api.VERSION]

    try:
      params = "?" + urlencode(
        tuple(
          dict(appid=self.appid, **api.PARAMS, **params).items()
        )
      )
    except TypeError:
      raise ParameterConflict("cannot pass a parameter specified by `API` object")

    base_url = url if url is not None else self.BASE_URL
    url = base_url + api_version + api.ENDPOINT + params
    resp = requests.get(url)
    return api.format_results(resp)

  # NOTE: Not all parameters are supported
  # Additionally, parameters produced by timeout and async related params are not easily accessible atm
  @overload
  def full_results_query(
    self,
    input: str,
    *,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...
  
  @overload
  def full_results_query(
    self,
    input: str,
    *,
    ip: str,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  @overload
  def full_results_query(
    self,
    input: str,
    *,
    latlong: LatLong,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  @overload
  def full_results_query(
    self,
    input: str,
    *,
    location: str,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  def full_results_query(self, input: str, **params) -> FullResults:
    format = params.pop("format", None)
    if format is not None:
      return self.query(api=FullResultsAPI, input=input, format=",".join(format), **params)
    else:
      return self.query(api=FullResultsAPI, input=input, **params)

  @overload
  def conversational_query(
    self,
    i: str,
    *,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  @overload
  def conversational_query(
    self,
    i: str,
    *,
    conversationalID: str,
    url: str,
    s: Optional[int] = None,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  def conversational_query(self, i: str, **params) -> ConversationalResults:
    return self.query(api=ConversationalAPI, i=i, **params)

  @overload
  def conversational_followup_query(
    self,
    i: str,
    result: ConversationalResults,
    *,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  def conversational_followup_query(self, i: str, result: ConversationalResults, **params):
    return self.conversational_query(i=i, url=result.followup_url, **result.followup_params, **params)

  @overload
  def simple_query(
    self,
    i: str,
    *,
    layout: Optional[str] = None,
    background: Optional[str] = None,
    foreground: Optional[str] = None,
    fontsize: Optional[int] = None,
    width: Optional[int] = None,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> SimpleImage:
    ...

  def simple_query(self, i: str, **params) -> SimpleImage:
    return self.query(api=SimpleAPI, i=i, **params)

  @overload
  def short_query(
    self,
    i: str,
    *,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> str:
    ...

  def short_query(self, i: str, **params) -> str:
    return self.query(api=ShortAPI, i=i, **params)

  @overload
  def spoken_query(
    self,
    i: str,
    *,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> str:
    ...
  
  def spoken_query(self, i: str, **params) -> str:
    return self.query(api=SpokenAPI, i=i, **params)



class AsyncClient(ClientBase):
  """Async client to interact with the APIs, powered by aiohttp"""

  async def query(self, api: API, url: Optional[str] = None, **params):
    if not isinstance(api, API):
      raise TypeError("api must be `API` type")


    if api.VERSION not in self.API_VERSION.keys():
      raise ValueError(f"Unknown API version '{request.version}'.")

    api_version = self.API_VERSION[api.VERSION]

    try:
      params = "?" + urlencode(
        tuple(
          dict(appid=self.appid, **api.PARAMS, **params).items()
        )
      )
    except TypeError:
      raise ParameterConflict("cannot pass a parameter specified by `API` object")
      
    base_url = url if url is not None else self.BASE_URL
    url = base_url + api_version + api.ENDPOINT + params
    async with aiohttp.ClientSession() as client:
      async with client.get(url) as resp:
        result = await api.async_format_results(resp)
    return result

  # NOTE: Not all parameters are supported
  # Additionally, parameters produced by timeout and async related params are not easily accessible atm
  @overload
  async def full_results_query(
    self,
    input: str,
    *,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...
  
  @overload
  async def full_results_query(
    self,
    input: str,
    *,
    ip: str,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  @overload
  async def full_results_query(
    self,
    input: str,
    *,
    latlong: LatLong,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  @overload
  async def full_results_query(
    self,
    input: str,
    *,
    location: str,
    format: Optional[Sequence[str, ...]] = None,
    podindex: Optional[Sequence[int, ...]] = None,
    reinterpret: Optional[Bool] = None,
    translation: Optional[Bool] = None,
    ignorecase: Optional[Bool] = None,
    assumption: Optional[str] = None,
    units: Optional[Units] = None,
    **params
  ) -> FullResults:
    ...

  async def full_results_query(self, input: str, **params) -> FullResults:
    format = params.pop("format", None)
    if format is not None:
      return await self.query(api=FullResultsAPI, input=input, format=",".join(format), **params)
    else:
      return await self.query(api=FullResultsAPI, input=input, **params)

  @overload
  async def conversational_query(
    self,
    i: str,
    *,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  @overload
  async def conversational_query(
    self,
    i: str,
    *,
    conversationalID: str,
    url: str,
    s: Optional[int] = None,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  async def conversational_query(self, i: str, **params) -> ConversationalResults:
    return await self.query(api=ConversationalAPI, i=i, **params)
  
  @overload
  async def conversational_followup_query(
    self,
    i: str,
    result: ConversationalResults,
    *,
    geolocation: Optional[str] = None,
    ip: Optional[str] = None,
    units: Optional[Units] = None
  ) -> ConversationalResults:
    ...

  async def conversational_followup_query(self, i: str, result: ConversationalResults, **params):
    return await self.conversational_query(i=i, url=result.followup_url, **result.followup_params, **params)

  @overload
  async def simple_query(
    self,
    i: str,
    *,
    layout: Optional[str] = None,
    background: Optional[str] = None,
    foreground: Optional[str] = None,
    fontsize: Optional[int] = None,
    width: Optional[int] = None,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> SimpleImage:
    ...

  async def simple_query(self, i: str, **params) -> SimpleImage:
    return await self.query(api=SimpleAPI, i=i, **params)

  @overload
  async def short_query(
    self,
    i: str,
    *,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> str:
    ...

  async def short_query(self, i: str, **params) -> str:
    return await self.query(api=ShortAPI, i=i, **params)

  @overload
  async def spoken_query(
    self,
    i: str,
    *,
    units: Optional[Units] = None,
    timeout: Optional[int] = None
  ) -> str:
    ...
  
  async def spoken_query(self, i: str, **params) -> str:
    return await self.query(api=SpokenAPI, i=i, **params)