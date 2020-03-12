# -------------------------------------------------------------------------------
# (c) 2019-2020 Siemens AG
# All Rights Reserved.
# Author: gernot.hillier@siemens.com
#
# Licensed as Siemens Inner Source, see top-level License.md file for details.
# -------------------------------------------------------------------------------

"""High-Level Python interface to the SW360 REST API. This is a set of Python
classes abstracting most important aspects of the SW360 REST API. For now, this
does NOT strive to provide a complete API abstraction, just provide a more
convenient abstraction for some (important) objects."""


class Release:
    """A release is the SW360 abstraction for a single version of a component.

    You can either create it from a SW360 `json` object or by specifying the
    details via the constructor parameters, see list below. Only the most
    important attributes are supported, rest hast be provided via `kwargs` and
    is stored in the `details` attribute of instances.

    For JSON parsing, please read documentation of from_json() method.

    :param json: create release from SW360 JSON object by calling from_json()
    :param component_id: SW360 id of the component the release belongs to
    :param version: the actual version
    :param downloadurl: URL the release was downloaded from
    :param kwargs: additional relase details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type component_id: string
    :type version: string
    :type downloadurl: string
    :type kwargs: dictionary

    """
    def __init__(self, json=None, component_id=None, version=None,
                 downloadurl=None, **kwargs):
        self.details = {}
        """All release details which are not explicitely supported by the
        constructor parameters are stored in the `details` attribute. Shall use
        names and types as specified in SW360 REST API."""

        if json is not None:
            self.from_json(json)
        else:
            self.component_id = component_id
            self.version = version
            self.downloadurl = downloadurl
            for key, value in kwargs:
                self.details[key] = value

    def from_json(self, json):
        """Parse release JSON object from SW360 REST API. The component it
        belongs to will be extracted and stored in the `component_id`
        attribute.

        All details not directly supported by this class will be stored as-is
        in the `details` instance attribute. For now, this also includes
        attachment information and external ids which will be stored as-is in
        `details['_embedded']['sw360:attachments']` and
        `details['externalIds'].  Please note that this might change in future
        if better abstractions will be added in this Python library."""
        for key, value in json.items():
            if key in ("name", "version", "downloadurl"):
                self.__setattr__(key, value)
            elif key == "_links":
                for links_key, links_value in value.items():
                    if links_key == "sw360:component":
                        self.component_id = links_value["href"].split("/")[-1]
                    elif links_key == "self":
                        self.id = links_value["href"].split("/")[-1]
                    else:
                        self.details.setdefault(key, {})
                        self.details[key][links_key] = links_value
            else:
                self.details[key] = value

    def __repr__(self):
        """Representation string."""
        return "<Release %s %s id:%s>" % (self.name, self.version, self.id)


class Component:
    """A component is the SW360 abstraction for a single software
    package/library/program/etc.

    You can either create it from a SW360 `json` object or by specifying the
    details via the constructor parameters, see list below. Only the most
    important attributes are supported, rest hast be provided via `kwargs` and
    is stored in the `details` attribute of instances.

    For JSON parsing, please read documentation of from_json() method.

    :param json: create component from SW360 JSON object by calling from_json()
    :param name: name of the component
    :param description: short description for component
    :param homepage: homepage of the component
    :param component_type: one of "INTERNAL", "OSS", "COTS", "FREESOFTWARE",
                           "INNER_SOURCE", "SERVICE", "CODE_SNIPPET"
    :param kwargs: additional component details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type name: string
    :type description: string
    :type homepage: string
    :type component_type: string
    :type kwargs: dictionary
    """
    def __init__(self, json=None, name=None, description=None, homepage=None,
                 component_type=None, **kwargs):
        self.details = {}
        """All release details which are not explicitely supported by the
        constructor parameters are stored in the `details` attribute. Shall use
        names and types as specified in SW360 REST API."""

        self.releases = {}

        if json is not None:
            self.from_json(json)
        else:
            self.name = name
            self.description = description
            self.homepage = homepage
            self.component_type = component_type
            for key, value in kwargs:
                self.details[key] = value

    def from_json(self, json):
        """Parse component JSON object from SW360 REST API. Information for
        its releases will be extracted, Release() objects created for them
        and stored in the `releases` instance attribue. Please note that
        the REST API will only provide basic information for the releases.

        All details not directly supported by this class will be
        stored as-is in the `details` instance attribute. For now, this also
        includes vendor information and external ids which will be stored
        as-is in `details['_embedded']['sw360:vendors']` and
        `details['externalIds'].  Please note that this might change in future
        if better abstractions will be added in this Python library."""
        releases = None
        for key, value in json.items():
            if key in ("name", "description", "homepage"):
                self.__setattr__(key, value)
            elif key == "componentType":
                self.component_type = value
            elif key in ("_links", "_embedded"):
                for links_key, links_value in value.items():
                    if key == "_links" and links_key == "self":
                        self.id = links_value["href"].split("/")[-1]
                    elif links_key == "sw360:releases":
                        releases = links_value
                    else:
                        self.details.setdefault(key, {})
                        self.details[key][links_key] = links_value
            else:
                self.details[key] = value

        if releases is None:
            return

        for release_json in releases:
            release = Release(component_id=self.id)
            release.from_json(release_json)
            self.releases[release.id] = release

    def __repr__(self):
        """Representation string."""
        return "<Component %s id:%s>" % (self.name, self.id)
