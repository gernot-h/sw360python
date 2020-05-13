# -------------------------------------------------------------------------------
# (c) 2019-2020 Siemens AG
# All Rights Reserved.
# Author: gernot.hillier@siemens.com
#
# Licensed as Siemens Inner Source, see top-level License.md file for details.
# -------------------------------------------------------------------------------

import re

"""Preview of High-Level, object oriented Python interface to the SW360 REST API.
For now, this does NOT strive to be stable or complete. Feel free to use it as
a more convenient abstraction for some (important) objects, but be prepared for
changes."""


class SW360Resource:
    """Base class representing an SW360 resource like project, component,
    release etc.
    """

    def __init__(self, json=None, resource_id=None, **kwargs):
        self.details = {}
        """All resource details which are not explicitely supported by the
        constructor parameters of the derived objexts are stored in the
        `details` attribute. Shall use names and types as specified in SW360
        REST API."""

        self.id = resource_id
        """All SW360 resource instances have an `id`. If it is set to `None`,
        the object is yet unknown to SW360 - otherwise, it stores the SW360
        id (release_id, component_id, etc.)."""

        for key, value in kwargs.items():
            self.details[key] = value

        if json is not None:
            self.from_json(json)

    def _parse_release_list(self, json_list, component_id=None):
        """Parse a JSON list of releases, create according objects and add
        them to `container`."""
        releases = {}
        for release_json in json_list:
            release = Release(component_id=component_id)
            release.from_json(release_json)
            releases[release.id] = release
        return releases

    def _parse_attachment_list(self, json_list, resources=[]):
        """Parse a JSON list of releases, create according objects and add
        them to `container`."""
        attachments = {}
        for attachment_json in json_list:
            attachment = Attachment(resources=resources)
            attachment.from_json(attachment_json)
            attachments[attachment.id] = attachment
        return attachments

    def _parse_link(self, key, links_key, links_value):
        """Parse a _links or _embedded section in JSON"""
        if links_key == "sw360:component":
            self.component_id = links_value["href"].split("/")[-1]
        elif links_key == "sw360:downloadLink":
            self.download_link = links_value["href"]
        elif links_key == "sw360:attachments":
            self.attachments = self._parse_attachment_list(
                links_value,
                resources=[self])
        elif links_key == "sw360:releases":
            self.releases = self._parse_release_list(
                links_value,
                component_id=self.id)
        elif links_key == "self":
            self.id = links_value["href"].split("/")[-1]
        else:
            self.details.setdefault(key, {})
            self.details[key][links_key] = links_value

    _camel_case_pattern = re.compile(r'(?<!^)(?=[A-Z])')

    def from_json(self, json, copy_attributes=list(), snake_case=True):
        """`copy_attributes` will be copied as-is between this instance's
        attributes and JSON members. If `snake_case` is set, more Python-ish
        snake_case names will be used (project_type instead of projectType).
        """
        for key, value in json.items():
            if key in copy_attributes:
                if snake_case:
                    key = self._camel_case_pattern.sub('_', key).lower()
                self.__setattr__(key, value)
            elif key in ("_links", "_embedded"):
                for links_key, links_value in value.items():
                    self._parse_link(key, links_key, links_value)
            else:
                self.details[key] = value


class Release(SW360Resource):
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
    :param release_id: id of the release (if exists in SW360 already)
    :param kwargs: additional relase details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type component_id: string
    :type version: string
    :type downloadurl: string
    :type release_id: string
    :type kwargs: dictionary
    """
    def __init__(self, json=None, release_id=None, component_id=None,
                 version=None, downloadurl=None, **kwargs):
        self.attachments = {}

        self.component_id = component_id
        self.version = version
        self.downloadurl = downloadurl
        super().__init__(json, release_id, **kwargs)

    def from_json(self, json):
        """Parse release JSON object from SW360 REST API. The component it
        belongs to will be extracted and stored in the `component_id`
        attribute.

        All details not directly supported by this class will be stored as-is
        in the `details` instance attribute. For now, this also includes
        external ids which will be stored as-is in `details['externalIds'].
        Please note that this might change in future if better abstractions
        will be added in this Python library."""
        super().from_json(
            json,
            copy_attributes=("name", "version", "downloadurl"))

    def __repr__(self):
        """Representation string."""
        return "<Release %s %s id:%s>" % (self.name, self.version, self.id)


class Attachment(SW360Resource):
    """An attachment is used to store all kinds of files in SW360, for example
    upstream source files (attachment_type "SOURCE"), self-created source file bundles
    ("SOURCE_SELF"), clearing reports ("CLEARING_REPORT") or CLI files
    ("COMPONENT_LICENSE_INFO_XML").

    You can either create it from a SW360 `json` object or by specifying the
    details via the constructor parameters, see list below. Only the most
    important attributes are supported, rest hast be provided via `kwargs` and
    is stored in the `details` attribute of instances.

    For JSON parsing, please read documentation of from_json() method.

    :param json: create release from SW360 JSON object by calling from_json()
    :param attachment_id: SW360 id of the attachment (if it exists already)
    :param resources: dictionary of SW360 resource objects the attachment belongs to
                      (instances of Release(), Component() or Project() with id as key)
    :param filename: the filename of the attachment
    :param sha1: SHA1 sum of the file to check its integrity
    :param attachment_type: one of "DOCUMENT", "SOURCE", "SOURCE_SELF"
           "CLEARING_REPORT", "COMPONENT_LICENSE_INFO_XML", "BINARY",
           "BINARY_SELF", "LICENSE_AGREEMENT", "README_OSS"
    :param kwargs: additional relase details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type attachment_id: string
    :type release_id: string
    :type filename: string
    :type sha1: string
    :type attachment_type: string
    :type kwargs: dictionary
    """
    def __init__(self, json=None, attachment_id=None, resources={},
                 filename=None, sha1=None, attachment_type=None, **kwargs):
        self.resources = resources
        self.filename = filename
        self.sha1 = sha1
        self.attachment_type = attachment_type
        self.download_link = None
        super().__init__(json, attachment_id, **kwargs)

    def from_json(self, json):
        """Parse attachment JSON object from SW360 REST API. For now, we don't
        support parsing the resource the attachment belongs to, so this needs
        to be set via constructur.

        All details not directly supported by this class will be stored as-is
        in the `details` instance attribute.
        Please note that this might change in future if more abstractions
        will be added in this Python library."""
        super().from_json(
            json,
            copy_attributes=("filename", "sha1", "attachmentType",
                             "createdBy", "createdTeam", "createdComment", "createdOn",
                             "checkedBy", "checkedTeam", "checkedComment", "checkedOn",
                             "checkStatus"))

    def __repr__(self):
        """Representation string."""
        return "<Attachment %s id:%s>" % (self.filename, self.id)


class Component(SW360Resource):
    """A component is the SW360 abstraction for a single software
    package/library/program/etc.

    You can either create it from a SW360 `json` object or by specifying the
    details via the constructor parameters, see list below. Only the most
    important attributes are supported, rest hast be provided via `kwargs` and
    is stored in the `details` attribute of instances.

    For JSON parsing, please read documentation of from_json() method.

    :param json: create component from SW360 JSON object by calling from_json()
    :param component_id: id of the component (if exists in SW360 already)
    :param name: name of the component
    :param description: short description for component
    :param homepage: homepage of the component
    :param component_type: one of "INTERNAL", "OSS", "COTS", "FREESOFTWARE",
                           "INNER_SOURCE", "SERVICE", "CODE_SNIPPET"
    :param kwargs: additional component details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type component_id: string
    :type name: string
    :type description: string
    :type homepage: string
    :type component_type: string
    :type kwargs: dictionary
    """
    def __init__(self, json=None, component_id=None, name=None, description=None,
                 homepage=None, component_type=None, **kwargs):
        self.releases = {}
        self.attachments = {}

        self.name = name
        self.description = description
        self.homepage = homepage
        self.component_type = component_type
        super().__init__(json, component_id, **kwargs)

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
        super().from_json(
            json,
            copy_attributes=("name", "description", "homepage",
                             "componentType"))

    def __repr__(self):
        """Representation string."""
        return "<Component %s id:%s>" % (self.name, self.id)


class Project(SW360Resource):
    """A project is SW360 abstraction for a collection of software components
    used in a project/product. It can contain links to other `Project`s or
    `Release`s.

    You can either create it from a SW360 `json` object or by specifying the
    details via the constructor parameters, see list below. Only the most
    important attributes are supported, rest hast be provided via `kwargs` and
    is stored in the `details` attribute of instances.

    For JSON parsing, please read documentation of from_json() method.

    :param json: create component from SW360 JSON object by calling from_json()
    :param project_id: id of the project (if exists in SW360 already)
    :param name: name of the project
    :param version: version of the project
    :param description: short description for project
    :param visibility: project visibility in SW360, one of "PRIVATE",
                       "ME_AND_MODERATORS", "BUISNESSUNIT_AND_MODERATORS",
                       "EVERYONE"
    :param project_type: one of "CUSTOMER", "INTERNAL", "PRODUCT", "SERVICE",
                         "INNER_SOURCE"
    :param kwargs: additional project details as specified in the SW360 REST API
    :type json: SW360 JSON object
    :type project_id: string
    :type name: string
    :type version: string
    :type description: string
    :type visibility: string
    :type project_type: string
    :type kwargs: dictionary
    """
    def __init__(self, json=None, project_id=None, name=None, version=None,
                 description=None, visibility=None, project_type=None,
                 **kwargs):
        self.releases = {}

        self.name = name
        self.version = version
        self.description = description
        self.visibility = visibility
        self.project_type = project_type
        super().__init__(json, project_id, **kwargs)

    def from_json(self, json):
        """Parse project JSON object from SW360 REST API. Information for
        its releases will be extracted, Release() objects created for them
        and stored in the `releases` instance attribue. Please note that
        the REST API will only provide basic information for the releases.

        All details not directly supported by this class will be
        stored as-is in the `details` instance attribute. For now, this also
        includes linked projects and external ids. Please note that this might
        change in future if better abstractions will be added in this Python
        library."""
        super().from_json(
            json,
            copy_attributes=("name", "description", "version", "visibility",
                             "projectType"))

    def __repr__(self):
        """Representation string."""
        return "<Project %s id:%s>" % (self.name, self.id)
