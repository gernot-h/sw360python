import responses
import unittest
from tests.test_sw360obj_base import Sw360ObjTestBase, SW360_BASE_URL
from sw360 import Component


class Sw360ObjTestComponent(Sw360ObjTestBase):
    @responses.activate
    def test_get_component(self):
        responses.add(
            responses.GET,
            SW360_BASE_URL + "components/123",
            json={
                'name': 'acl',
                'somekey': 'value',
                '_embedded': {
                    'sw360:releases': [{
                        'name': 'acl',
                        'version': '2.2',
                        '_links': {'self': {
                            'href': SW360_BASE_URL + 'releases/7c4'}}}]}})
        comp = Component().get(self.lib, "123")
        self.assertEqual(comp.name, "acl")
        self.assertEqual(comp.details["somekey"], "value")
        self.assertEqual(len(comp.releases), 1)
        self.assertEqual(comp.releases["7c4"].component_id, "123")


if __name__ == "__main__":
    unittest.main()
