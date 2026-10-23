"""Opt-in cylinder-X geography and legacy compatibility contracts."""
import unittest

from app.planet_generation import (_finish_planet, _periodic_noise, generate_planet_v6,
                                   validate_surface)
from app.universe import build_universe


class PlanetV6Tests(unittest.TestCase):
    def test_periodic_noise_and_all_presets_validate(self):
        for scale in (11, 13, 19, 23, 31):
            for x in (-129, -1, 0, 37, 127):
                self.assertEqual(_periodic_noise(17, "qa", x, 29, scale),
                                 _periodic_noise(17, "qa", x+128, 29, scale))
        for preset in ("continental", "archipelago", "oceanic", "arid", "barren", "frozen"):
            geo=generate_planet_v6("v6", 71, preset)
            validate_surface(geo)
            self.assertEqual((geo["planet"]["width"],geo["planet"]["height"]),(128,80))
            self.assertEqual(len(geo["provinces"]),40)
            self.assertEqual(geo["surface"]["topology"],"cylinder-x")
            self.assertEqual(geo,generate_planet_v6("v6",71,preset))

    def test_single_outlet_across_seam_and_wrapped_river_paths(self):
        width,height=128,80
        elevation=[500]*(width*height)
        outlet=40*width
        elevation[outlet]=380
        geo=_finish_planet("seam",1,"terrestrial",elevation,"planet-v6",width=width,height=height,
                           province_size=16,surface_preset="continental",wrap_x=True)
        geo["surface"].update({"version":"planet-v6","preset":"continental",
                               "hydrology":"ocean-draining","topology":"cylinder-x"})
        validate_surface(geo)
        self.assertEqual(geo["surface"]["drainage"][outlet+width-1],outlet)
        self.assertEqual(geo["terrain_grid"][outlet+width-1],"c")
        self.assertTrue(any(any(abs(a[0]-b[0])==width-1 for a,b in zip(river["points"],river["points"][1:]))
                            for river in geo["surface"]["rivers"]))

    def test_topology_is_required_and_malformed_seam_edges_fail(self):
        geo=generate_planet_v6("v6",91,"continental")
        missing={**geo,"surface":dict(geo["surface"])}
        del missing["surface"]["topology"]
        with self.assertRaises(ValueError): validate_surface(missing)
        broken={**geo,"surface":dict(geo["surface"])}
        broken["surface"]["drainage"]=list(geo["surface"]["drainage"])
        # A seam-crossing parent is valid only when it is the actual drainage neighbor.
        i=0
        broken["surface"]["drainage"][i]=2
        with self.assertRaises(ValueError): validate_surface(broken)

    def test_new_world_private_config_and_legacy_default(self):
        old=build_universe("v6-default",123)
        self.assertEqual(old["_private"]["generator_config"]["planet"],"planet-v1")
        self.assertTrue(all("surface" not in g for g in old["geography"].values()))
        state=build_universe("v6-world",123,planet_generator="planet-v6",preset="continental")
        self.assertEqual(state["_private"]["generator_config"]["planet"],"planet-v6")
        self.assertTrue(all(g["surface"]["version"]=="planet-v6" for g in state["geography"].values()))
        self.assertEqual(state["_private"]["generator_config"]["grid"],"grid128x80")


if __name__=="__main__":
    unittest.main()
