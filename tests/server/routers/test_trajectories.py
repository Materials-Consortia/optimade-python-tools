from optimade.models import PartialDataResponse

from ..utils import NoJsonEndpointTests


class Test_traj_data(NoJsonEndpointTests):
    request_str = "http://example.org/partial_data/6509be05a54743f440a7f36b?response_fields=cartesian_site_positions&response_format=jsonlines&property_ranges=dim_frames:1:40000:2,dim_sites:1:32:1,dim_cartesian_dimensions:1:3:1"
    response_cls = PartialDataResponse


def test_trajectories(
    check_response,
):
    expected_ids = ["6509be05a54743f440a7f36b"]
    request = "/trajectories?filter=nelements=1"
    check_response(request, expected_ids)
    pass

    # request = "/trajectories?filter=nelements==1"
    # expected_ids = ["62696ac7eef0323c842f9f51"]
    # check_response(request, expected_ids=expected_ids)
    #
    # # Because the amount of data that will be returned is limited to reduce waiting times. # TODO Once I have created a proper config parameter for this I should use this maximum package size to determine whether one or two entries are returned.
    # request = "/trajectories?filter=nelements>=6&response_fields=cartesian_site_positions,_exmpl_time&last_frame=40&first_frame=5"
    # expected_ids = ["62696ac7eef0323c842f9f51"]
    # check_response(
    #     request, expected_ids=expected_ids, expected_return=2
    # )
