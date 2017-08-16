# nickyabbot repository

[![](https://images.microbadger.com/badges/image/karmab/nickyabbot.svg)](https://microbadger.com/images/karmab/nickyabbot "Get your own image badge on microbadger.com")
![Super Dope](https://img.shields.io/badge/karmab-super%20dope-b9f2ff.svg)

Telegram Troll Bot

## Requisites

- tekegram api token
- giphy api key ( optional)

Then i use 

```
docker run --name=trollbot -v ~/troll.db:/root/troll.db -v ~/staticquotes.txt:/root/staticquotes.txt -e TOKEN=$TOKEN -d  karmab/nickyabbot
```

or the following with a giphy api key

```
docker run --name=trollbot -v ~/troll.db:/root/troll.db -v ~/staticquotes.txt:/root/staticquotes.txt -e TOKEN=$TOKEN -e GIHPYKEY=$GIPHYKEY -d  karmab/nickyabbot
```

## TODO

- Read The docs
- Cool things

## Copyright

Copyright 2017 Karim Boumedhel

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Problems?

Send me a mail at [karimboumedhel@gmail.com](mailto:karimboumedhel@gmail.com) !

Mac Fly!!!

karmab
