import responses
import unittest
from tests.test_sw360obj_base import Sw360ObjTestBase, SW360_BASE_URL
from sw360 import Project


class Sw360ObjTestProject(Sw360ObjTestBase):
    @responses.activate
    def test_get_project(self):
        responses.add(
            responses.GET,
            SW360_BASE_URL + "projects/123",
            json={
                'name': 'MyProj',
                'version': '11.0',
                '_embedded': {
                    'sw360:releases': [{
                        'name': 'acl',
                        'version': '2.2',
                        '_links': {'self': {
                            'href': SW360_BASE_URL + 'releases/7c4'}}}]}})
        proj = Project().get(self.lib, "123")
        self.assertEqual(proj.name, "MyProj")
        self.assertEqual(proj.version, "11.0")
        self.assertEqual(len(proj.releases), 1)
        self.assertIsNone(proj.releases["7c4"].component_id)


if __name__ == "__main__":
    unittest.main()
