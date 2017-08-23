manually

```
oc new-app karmab/nickyabbot -e TOKEN=$TOKEN -e GIPHYKEY=$GIPHYKEY
POD=`oc get pod -o name -l app=nickyabbot | sed 's@pods/@@'`
oc volume dc/nickyabbot --add --name=troll --type=persistentVolumeClaim  --claim-name=pvctroll --mount-path=/tmp/troll --containers=nickyabbot
oc rsync /tmp/troll/ $POD:/tmp/troll
```
