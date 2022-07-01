def test_trajectories(
    check_response,
):  # TODO check whether there is a better place to put these tests
    request = "/trajectories?filter=nelements<6&response_fields=cartesian_site_positions,_exmpl_time&last_frame=40&first_frame=5"
    expected_ids = [
        "622a07fa8544a62c55ef087a",
        "622a29c4087ac20730106f33",
        "622b548fe73216ae229b188b",
    ]
    check_response(request, expected_ids=expected_ids)

    request = "/trajectories?filter=nelements>=6&response_fields=cartesian_site_positions,_exmpl_time&last_frame=40&first_frame=5"
    expected_ids = ["62696ac7eef0323c842f9f51"]
    check_response(
        request, expected_ids=expected_ids, expected_return=2
    )  # Because the amount of data that will be returned is limited to reduce waiting times. # TODO Once I have created a proper config parameter for this I should use this maximum package size to determine whether one or two entries are returned.
