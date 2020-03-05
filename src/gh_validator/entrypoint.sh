#!/bin/sh

# Retrieve and add GitHub Actions host runner IP to known hosts
DOCKER_HOST_IP=$(cat /docker_host_ip)
echo ${DOCKER_HOST_IP} gh_actions_host >> /etc/hosts

run_validator="optimade_validator"

if [ ! -z "${INPUT_PORT}" ]; then
    BASE_URL="${INPUT_PROTOCOL}://${INPUT_DOMAIN}:${INPUT_PORT}"
else
    BASE_URL="${INPUT_PROTOCOL}://${INPUT_DOMAIN}"
fi
run_validator="${run_validator} ${BASE_URL}"

index=""
case ${INPUT_INDEX} in
    y | Y | yes | Yes | YES | true | True | TRUE | on | On | ON)
        index=" --index"
        ;;
    n | N | no | No | NO | false | False | FALSE | off | Off | OFF)
        ;;
    *)
        echo "Non-valid input for 'index': ${INPUT_INDEX}. Will use default (false)."
        ;;
esac

case ${INPUT_ALL_VERSIONED_PATHS} in
    y | Y | yes | Yes | YES | true | True | TRUE | on | On | ON)
        for version in '0' '0.10' '0.10.1'; do
            if [ "${INPUT_PATH}" = "/" ]; then
                sh -c "${run_validator}${INPUT_PATH}v${version}${index}"
            else
                sh -c "${run_validator}${INPUT_PATH}/v${version}${index}"
            fi
        done
        ;;
    n | N | no | No | NO | false | False | FALSE | off | Off | OFF)
        run_validator="${run_validator}${INPUT_PATH}${index}"
        sh -c "${run_validator}"
        ;;
    *)
        echo "Non-valid input for 'all versioned paths': ${INPUT_ALL_VERSIONED_PATHS}. Will use default (false)."
        run_validator="${run_validator}${INPUT_PATH}${index}"
        sh -c "${run_validator}"
        ;;
esac
