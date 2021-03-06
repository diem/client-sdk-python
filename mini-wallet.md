## Try MiniWallet

Install the Diem Python SDK with MiniWallet and MiniWallet Test Suite (included since version 1.2.6):
```
pip install diem[all]
```
You may need to use quotes `pip install 'diem[all]'`.

To include the Diem MiniWallet in a pip requirements.txt file add:
```
diem[all]>=1.2.6
```


Once the pip install command above has run, the `dmw` cli will be installed in your pip enviroment.

To see available sub-commands:
```
dmw --help
```

You may start a MiniWallet server (connects to Diem testnet by default)
```
dmw start-server
```

Open http://localhost:8888 to check MiniWallet API specification document (Defined by OpenAPI Specification 3.0.3).
The document includes simple examples to try out the MiniWallet API.

A hosted version of the API specification document is located at [here](https://diem.github.io/client-sdk-python/mini-wallet-api-spec.html).

`start-server` options:

```
dmw start-server --help
Usage: dmw start-server [OPTIONS]

Options:
  -n, --name TEXT                 Application name.  [default: mini-wallet]
  -h, --host TEXT                 Start server host.  [default: localhost]
  -p, --port INTEGER              Start server port.  [default: 8888]
  -j, --jsonrpc TEXT              Diem fullnode JSON-RPC URL.  [default:
                                  http://testnet.diem.com/v1]

  -f, --faucet TEXT               Testnet faucet URL.  [default:
                                  http://testnet.diem.com/mint]

  -l, --logfile TEXT              Log to a file instead of printing into
                                  console.

  -o, --enable-debug-api BOOLEAN  Enable debug API.  [default: True]
  --help                          Show this message and exit.
```


## MiniWallet Test Suite

Try out the MiniWallet Test Suite by hitting the target server we started by `dmw start-server`
```
dmw test --target http://localhost:8888
```
You should see something like this:

```
> dmw test
Diem JSON-RPC URL: http://testnet.diem.com/v1
Diem Testnet Faucet URL: http://testnet.diem.com/mint
======================================== test session starts ===============================================
…...
collected 61 items

src/diem/testing/suites/test_miniwallet_api.py ......................ss.                              [ 40%]
src/diem/testing/suites/test_payment.py ....................................                          [100%]

============================== 59 passed, 2 skipped, 198 deselected in 18.26s ===============================
```

Follow the MiniWallet API specification to create a proxy server for your wallet application.
Assuming you're running your application at port 9999, you may run the MiniWallet Test Suite using this command:
```
dmw test --target http://localhost:9999
```

`test` options:
```
dmw test --help
Usage: dmw test [OPTIONS]

Options:
  -t, --target TEXT             Target mini-wallet application URL.  [default:
                                http://localhost:8888]

  -j, --jsonrpc TEXT            Diem fullnode JSON-RPC URL.  [default:
                                http://testnet.diem.com/v1]

  -f, --faucet TEXT             Testnet faucet URL.  [default:
                                http://testnet.diem.com/mint]

  --pytest-args TEXT            Additional pytest arguments, split by empty
                                space, e.g. `--pytest-args '-v -s'`.

  -d, --test-debug-api BOOLEAN  Run tests for debug APIs.  [default: False]
  -v, --verbose BOOLEAN         Enable verbose log output.  [default: False]
  --help                        Show this message and exit.
```

### How it works

1. The test suite is located in the `diem.testing.suites` package and includes the pytest file `conftest.py`.
2. `dmw test` launches a pytest runner to run tests.
3. The `conftest.py` starts a stub MiniWallet as a counterparty service for testing payment with the target server specified by the `--target` option.


### Working with a local testnet

1. [Download](https://docs.docker.com/get-docker/) and install Docker and Docker Compose (comes with Docker for Mac and Windows).
2. Download Diem testnet docker compose config: https://github.com/diem/diem/blob/master/docker/compose/validator-testnet/docker-compose.yaml
3. Run `docker-compose -f <path to your validator-testnet/docker-compose.yaml file> up --detach`
   * A Faucet will be available at http://127.0.0.1:8000
   * A JSON-RPC server will be available at http://127.0.0.1:8080
4. Test your application with a local testnet: `dmw test --jsonrpc http://127.0.0.1:8080 --faucet http://127.0.0.1:8000 --target http://localhost:9999`

### Test Off-chain API

As the test counterparty wallet application server is started locally, you need make sure your wallet application's off-chain API can access the stub server using it's base_url: `http://localhost:<port>`.
If your wallet application is not running locally, you will need to setup a tunnel for your wallet application to access the stub server.
