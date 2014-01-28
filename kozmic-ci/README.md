Директория содержит файлы, необходимые для создания Docker-образа для Kozmic CI
с помощью Packer.

В качестве provisioner используется Chef, запускающий рецепт `unistorage:ci`.

Небольшая шпаркалка, как создать, запустить и запушить Docker-образ:

* `packer build ./packer-template`
* `cat ./image.tar | docker import - aromanovich/unistorage`
* `docker run -i -t -v=/path/to/unistorage/src/:/unistorage/ aromanovich/unistorage /bin/bash`
* `docker push aromanovich/unistorage`
