# DocumentDB — Connection Drivers

Language-specific driver snippets. All require:

- `global-bundle.pem` downloaded (`curl -s https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o global-bundle.pem`)
- Five required connection params: `tls=true`, `tlsCAFile=global-bundle.pem`, `replicaSet=rs0`, `readPreference=secondaryPreferred`, `retryWrites=false`

Set `DOCDB_URI` from your secret store with the required TLS, replica-set, read preference, and retry options. Replace `<db-name>` with your database name. **Create the client once at module scope** and reuse across requests — per-request clients cause connection spikes and high CPU.

## Python (PyMongo)

```python
import os

import pymongo

client = pymongo.MongoClient(
    os.environ["DOCDB_URI"]
)
db = client["<db-name>"]
db.command("ping")
```

## Node.js (MongoDB Driver)

```javascript
const { MongoClient } = require("mongodb");

const client = new MongoClient(
  process.env.DOCDB_URI,
  { tlsCAFile: "global-bundle.pem" }
);

await client.connect();
await client.db("admin").command({ ping: 1 });
```

## Java (MongoDB Driver 4.x)

Use `applyConnectionString` — do NOT use `applyToClusterSettings` with a single host (sets SINGLE mode and breaks failover):

```java
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;

MongoClientSettings settings = MongoClientSettings.builder()
    .applyConnectionString(new ConnectionString(
        System.getenv("DOCDB_URI")
    ))
    .applyToConnectionPoolSettings(b -> b.maxSize(10).maxWaitQueueSize(2))
    .build();
MongoClient client = MongoClients.create(settings);
```

Java requires the RDS bundle converted to a JKS truststore:

```bash
mydir=/tmp/certs && truststore=${mydir}/rds-truststore.jks
# Generate a strong, unique truststore password — never hardcode one.
# Store it in Secrets Manager / Parameter Store and reference it from your app config.
storepassword=$(openssl rand -base64 24) && mkdir -p ${mydir}

curl -sS "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem" > ${mydir}/global-bundle.pem
awk 'split_after==1{n++;split_after=0} /-----END CERTIFICATE-----/{split_after=1}{print > "rds-ca-" n ".pem"}' < ${mydir}/global-bundle.pem

for CERT in rds-ca-*; do
  alias=$(openssl x509 -noout -text -in $CERT | perl -ne 'next unless /Subject:/; s/.*(CN=|CN = )//; print')
  keytool -import -file ${CERT} -alias "${alias}" -storepass ${storepassword} -keystore ${truststore} -noprompt
  rm $CERT
done
```

JVM flags (reference the same `$storepassword` generated above — never hardcode it; source it from Secrets Manager / Parameter Store in production):

```
-Djavax.net.ssl.trustStore=/tmp/certs/rds-truststore.jks
-Djavax.net.ssl.trustStorePassword=$storepassword
```

## Go (mongo-driver)

```go
import (
    "context"; "crypto/tls"; "crypto/x509"; "os"
    "go.mongodb.org/mongo-driver/mongo"
    "go.mongodb.org/mongo-driver/mongo/options"
)

caCert, _ := os.ReadFile("global-bundle.pem")
pool := x509.NewCertPool()
pool.AppendCertsFromPEM(caCert)
tlsConfig := &tls.Config{RootCAs: pool}

uri := os.Getenv("DOCDB_URI")
opts := options.Client().ApplyURI(uri).SetTLSConfig(tlsConfig)
client, err := mongo.Connect(context.TODO(), opts)
```

## C# / .NET

Download the .p7b variant: `wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.p7b`

Validate the RDS CA **per-connection** — do not import it into the machine's system `Root` store (that needs admin rights, persists after exit, and affects every other app on the host).

```csharp
using MongoDB.Driver;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;

string uri = Environment.GetEnvironmentVariable("DOCDB_URI")
    ?? throw new InvalidOperationException("Set DOCDB_URI before starting.");

// Load the RDS bundle into a connection-scoped collection (no system store changes)
var caCerts = new X509Certificate2Collection();
caCerts.Import("global-bundle.p7b");

var settings = MongoClientSettings.FromConnectionString(uri);
settings.UseTls = true;
settings.SslSettings = new SslSettings {
    ServerCertificateValidationCallback = (sender, cert, chain, errors) => {
        chain.ChainPolicy.TrustMode = X509ChainTrustMode.CustomRootTrust;
        chain.ChainPolicy.CustomTrustStore.AddRange(caCerts);
        return chain.Build(new X509Certificate2(cert));
    }
};

var client = new MongoClient(settings);
```

## Ruby

```ruby
client = Mongo::Client.new('mongodb://<endpoint>:27017',
  database: '<db>', replica_set: 'rs0',
  read: { mode: :secondary_preferred },
  user: 'admin', password: '<pw>',
  ssl: true, ssl_verify: true, ssl_ca_cert: 'global-bundle.pem',
  retry_writes: false)
```

## mongosh (shell)

```bash
mongosh "$DOCDB_URI"
```

When tunneling from a local machine, add `--tlsAllowInvalidHostnames`:

```bash
mongosh --tls --tlsAllowInvalidHostnames --tlsCAFile global-bundle.pem \
  --host 127.0.0.1 --port 27017 --username admin --password '<pw>'
```
