#!/bin/bash
APP_NAME="public-md-to-anki-server"
sudo docker rm $APP_NAME -f || echo "failed to remove existing ssh server"

id=$(sudo docker run -dit --restart='always' \
--name $APP_NAME \
-p 17394:9376 \
$APP_NAME)
echo "ID = $id"

sudo docker logs -f "$id"

# --mount type=bind,source=/home/morphs/DOCKER_IMAGES/PowerPointInteractiveGamesGenerator/config.json,target=/home/config.json \

# sudo docker rm -f "spotify-dbus-controller"

# sudo docker run -it --privileged='true' --restart='always' \
# --name 'spotify-dbus-controller' \
# --network host \
# --mount type=bind,source=/run/user/1000/bus,target=/run/user/1000/bus \
# spotify-dbus-controller

#sudo docker logs -f $ID


# --volume /sys/fs/cgroup:/sys/fs/cgroup:ro \
# --volume /run/user/1000/bus:/run/user/1000/bus \
# --env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
#--volume /var/run/dbus:/var/run/dbus \
#--volume /run/dbus/system_bus_socket:/run/dbus/system_bus_socket \
