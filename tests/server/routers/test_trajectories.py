def test_trajectories(
    check_response,
):
    # TODO check whether there is a better place to put these tests
    expected_ids = [
        "6315fccf020663a5df695091",
        "6315f867d017d7a2190865a9",
        "6315e1cb84a0e586b3374284",
    ]

    request = "/trajectories/6315e1cb84a0e586b3374284"  # ?response_fields=cartesian_site_positions,species&first_frame=1&last_frame=2"
    check_response(request, expected_ids)

    expected_ids = [
        "622a07fa8544a62c55ef087a",
        "622a29c4087ac20730106f33",
        "622b548fe73216ae229b188b",
        "62696ac7eef0323c842f9f51",
        "traj001",
        "62c5ba5b9f61194d3ec44335",
    ]
    request = "/trajectories"
    check_response(request, expected_ids)

    request = "/trajectories?page_limit=4&response_fields=nframes,cartesian_site_positions,dimension_types,immutable_id,last_modified,reference_frame,species,species_at_sites,available_properties,lattice_vectors,reference_structure&page_offset=3&continue_from_frame=25"
    expected_ids = ["62696ac7eef0323c842f9f51", "traj001", "62c5ba5b9f61194d3ec44335"]
    check_response(request, expected_ids)

    request = "/trajectories?filter=nelements<6&response_fields=cartesian_site_positions,_exmpl_time&last_frame=40&first_frame=5"
    expected_ids = [
        "622a07fa8544a62c55ef087a",
        "622a29c4087ac20730106f33",
        "622b548fe73216ae229b188b",
        "62c5ba5b9f61194d3ec44335",
    ]
    check_response(request, expected_ids=expected_ids)

    # Because the amount of data that will be returned is limited to reduce waiting times. # TODO Once I have created a proper config parameter for this I should use this maximum package size to determine whether one or two entries are returned.
    # request = "/trajectories?filter=nelements>=6&response_fields=cartesian_site_positions,_exmpl_time&last_frame=40&first_frame=5"
    # expected_ids = ["62696ac7eef0323c842f9f51"]
    # check_response(
    #     request, expected_ids=expected_ids, expected_return=2
    # )
