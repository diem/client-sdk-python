## Diem MiniWallet



## Introduction

The Diem MiniWallet is a simplified wallet that can be run from the command line. You can use the Diem MiniWallet (and the included testing suite) to test your wallet application and to help develop your app to meet our requirements. 

The Diem MiniWallet connects to the Diem testnet by default. If you want to use the Diem MiniWallet to test in your local test network, read the instructions here. 



## Instal the Diem MiniWallet

1. Install the Diem Python SDK with the MiniWallet and it’s Test Suite (both included since version 1.2.6) using this command: `pip install diem[all]`. You may need to use quotes around `'diem[all]'`. 
You may need to use quotes `pip install 'diem[all]'`.

	To include the Diem MiniWallet in a pip requirements.txt file add:
	`diem[all]>=1.2.6`

2. Once you’ve run the pip install command, the Diem MiniWallet (dmw) CLI will be installed in your pip environment. To view the available CLI subcommands, run:
	`dmw --help`

## Start the Diem MiniWallet Server

The Diem MiniWallet server connects to the Diem testnet by default. To start the server, run:
`dmw start-server`


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

View the DiemMiniWallet API specification (OpenAPI Specification 3.0.3) by opening http://localhost:8888. These specs include simple examples to try out the MiniWallet API. A hosted version of the API specification document is also available [here](https://diem.github.io/client-sdk-python/mini-wallet-api-spec.html).


## Use the Diem MiniWallet Test Suite

The Diem MiniWallet Test Suite is a set of tests built on top of the Diem MiniWallet API and is used to validate a wallet app’s integration with the Diem Payment Network (DPN). 

Use the MiniWallet Test Suite to automate testing and checking if your wallet application meets our requirements. 

1. Hit the target server we started by `dmw start-server`:
	`dmw test --target http://localhost:8888` 

	You should see the following test report:

	```
	> dmw test
	Diem JSON-RPC URL: http://testnet.diem.com/v1
	Diem Testnet Faucet URL: http://testnet.diem.com/mint
	======================================== test session starts 						===============================================
	…...
	collected 61 items
	
	src/diem/testing/suites/test_miniwallet_api.py 										......................ss.                              [ 40%]
	src/diem/testing/suites/test_payment.py ....................................                          [100%]
	
	============================== 59 passed, 2 skipped, 198 deselected in 	18.26s ===============================
	```



2. Create a proxy server for your wallet application using the Diem MiniWallet API specification. Assuming you're running your application at port 9999, run the MiniWallet Test Suite using this command:

	```
	dmw test --target http://localhost:9999
	```

	`test` options:
	```
	dmw test --help
	Usage: dmw test [OPTIONS]
	
	Options:
    -t, --target TEXT               					Target mini-wallet application URL.
	                                  				[default: http://localhost:8888]	
	                                  				
	 -h, --stub-bind-host TEXT       					The host the miniwallet stub server will
	                                  				bind to  [default: localhost]
	                                  				
	 -p, --stub-bind-port INTEGER    					The port the miniwallet stub server will
	                             							bind to. Random if empty.
	                             							
	 -u, --stub-diem-account-base-url TEXT		The address that will be used for offchain
	                                  				callbacks. Defaults to
	                                 					http://localhost:{random_port}
	                                 					
	 -j, --jsonrpc TEXT              					Diem fullnode JSON-RPC URL.  [default:
	                                  				http://testnet.diem.com/v1]
	                                  				
	 -f, --faucet TEXT               					Testnet faucet URL.  [default:
	                                 				  http://testnet.diem.com/mint]
	                                 				  
	 --pytest-args TEXT              					Additional pytest arguments, split by empty
	                                  				space, e.g. `--pytest-args '-v -s'`
	                                  				
	 -d, --test-debug-api BOOLEAN    					Run tests for debug APIs.  [default: False]
	 
	 -v, --verbose                   					Enable verbose log output.  [default: False]
	 
	 --help                          					Show this message and exit.
	```



### How it works

The `diem.testing.suites` package contains the Diem MiniWallet Test Suite and includes the pytest file `conftest.py`.

Launch a pytest runner to run tests using:

`dmv test`

The `conftest.py` starts a stub MiniWallet as a counterparty service for testing payment with the target server specified by the --target option here.



### Work with your local test network

The Diem MiniWallet server connects to the Diem testnet by default. However, you can use the MiniWallet to test your wallet application in your own local test network as well.

To run your local test network:
1. Download and install [Docker](https://docs.docker.com/get-docker/) and Docker Compose (comes with Docker for Mac and Windows).
2. Download the [Diem testnet docker compose configuration file](https://github.com/diem/diem/blob/master/docker/compose/validator-testnet/docker-compose.yaml).
3. Run the following command: `docker-compose -f <path to your validator-testnet/docker-compose.yaml file> up --detach`
	* The Faucet service will now be available at http://127.0.0.1:8000.
	* A JSON-RPC server will now be available at http://127.0.0.1:8080.
4. Test your wallet application with your local test network using:
`dmw test --jsonrpc http://127.0.0.1:8080 --faucet http://127.0.0.1:8000 --target http://localhost:9999`

### Test Off-chain API

As the test counterparty wallet application server is started locally, you need make sure your wallet application's off-chain API can access the stub server using it's base_url: `http://localhost:<port>`.

If your wallet application is not running locally, you will need to setup a tunnel for your wallet application to access the stub server.