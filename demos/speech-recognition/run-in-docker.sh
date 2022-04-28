docker build -t aleph-speech-recognition .
docker run --rm -ti -v "$(pwd)":/usr/src/speech-recognition aleph-speech-recognition bash

# demos in de87afdfa4fd35c7d1a94e16f2c4827ecbd021a7c383ce45c62eefcf2ce9f531