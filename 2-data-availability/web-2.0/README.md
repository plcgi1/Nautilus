[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

# Proof of Web 2.0 Data Availability

```
name: study of web 2.0 data availability solution
type: research
status: updated draft
editor: Ocean Protocol Team
date: 01/31/2019
```

* [1. Introduction](#1-introduction)
* [2. Architecture](#2-architecture)
	+ [2.1 Data Provider Workflow](#21-data-provider-workflow)
	+ [2.2 Data Verifier Workflow](#22-data-verifier-workflow)
* [3. Amazon S3 as Storage](#3-amazon-s3-as-storage)
	+ [3.1 Data Attributes](#31-data-attributes)
	+ [3.2 AWS S3 Experiment](#32-aws-s3-experiment)
	+ [3.3 Required File Attributes in DDO](#33-required-file-attributes-in-ddo)
	  - [3.3.1 Syntax](#331-syntax)
	  - [3.3.2 file attributes stored in DDO](#332-file-attributes-stored-in-ddo)
* [4. Microsoft Azure as Storage](#4-microsoft-azure-as-storage)
	+ [4.1 Data Attributes](#41-data-attributes)
	+ [4.2 Azure Experiment](#42-azure-experiment)
	+ [4.3 Required File Attributes in DDO](#43-required-file-attributes-in-ddo)
	  - [4.3.1 Syntax](#431-syntax)
	  - [4.3.2 file attributes stored in DDO](#432-file-attributes-stored-in-ddo)
* [5. On-Premise Case](#5-on-premise-case)
	+ [5.1 Design](#51-design)
	+ [5.2 file attributes stored in DDO](#52-file-attributes-stored-in-ddo)
* [6. Reference](#6-reference)
* [7. License](#7-license)

## 1. Introduction

Nowadays the big volumes of data are typically stored in enterprise/organization silos in Big Data Lakers, Data Warehouse solutions or similar bespoke solutions.

This data is not publicly available and typically stored in:

* Cloud Providers (mostly Amazon and Azure)
* On-premise solutions
One of the requirements to ensure the "availability" of all datasets, which facilitates the mechanisms to retreive a Proof of Availability from cloud providers (p.e Amazon S3, Microsoft Azure) or on-premise (behind a HTTP service).

Ocean must provide the mechanisms to proof that data is available in these circumstances. Also needs to facilitate the procedure to external verifiers to validate that files included in the assets are available to be consumed.

The solution must not require to move the source data to make any calculation.

In the scope of this research task, it would be necessary to detail the possible solutions to put in place and the potential integration with Ocean architecture.

## 2. Architecture

Consider the solution cannot move or modify the source data, the most straightforward approach is **challenge-response solution**. The overall architecture shown in the below:

* **Data Provider**: the data owner who provides the dataset;
* **Data Verifer**: the data verifier who verifies the availability of dataset;
* **Smart Contract**: the Keeper contract deployed on blockchain network;
* **Ocean Off-Chain Query Component**: the off-chain query module that bridges the Keeper contract with cloud storage and OceanDB:
	* resolves the DID into DDO and extract `files` attribute;
	* query the checksum of each file from cloud provider (e.g., ETag of each file in S3)
	* calculate checksum of dataset as **SHA3 Hash** of ([list of all file checksums] + name + author + license + did)
* **OceanDB**: metadata-store that contains metadata information of datasets. 
* **Cloud Provider**: the data storage infrastructure that holds the raw data files such as AWS S3 and Azure.

<img src="img/architecture.jpg" width=1000 />

**Pros:**

* simple and implementable;
* no need to move or modify the data source;
* easy to integrate with Ocean.

**Cons:**

* require off-chain component to interact with cloud providers;
* all parties shall trust cloud providers to honestly return checksums. A potential attack vector is cloud providers store all checksums and simply lookup the needed checksum to return when queried. It fails the proof of availability;
* data providers must trust Ocean off-chain query component will not access or distribute datasets illegally, because they should grant data access to Ocean for future queries;

### 2.1 Data Provider Workflow

* Data provider registers the dataset to keeper contract on-chain (i.e., DID registry);
* Data provider stores the data source in AWS S3 or Azure and publish DDO in OceanDB;
* Data provider grants the data access to Ocean off-chain component (e.g., add it into the permission registry for cloud storage access);
* When dataset is registered, on-chain DID registration transaction emits an event message including DID;
* Ocean off-chain component listens to the event message and resolves the DID into DDO with OceanDB. 
* `list of files` attribute can be extracted from DDO. 
* Ocean off-chain component queries the checksums of these files from cloud storage.
* Cloud provider returns the corresponding checksums for data files (e.g., ETag for each file in S3);
* Ocean off-chain component calculates the dataset checksum with formula and updates the on-chain contract for this dataset;
* At this time, registration of dataset is complete and dataset is ready to be purchased.

### 2.2 Data Verifier Workflow

* Data verifier needs to register himself as an eligible verifier in Keeper contract;
* Verifier needs to send query of data availability (i.e., query availability of a specific DID) to Ocean off-chain component;
* Ocean off-chain component first validates the identity of verifier with on-chain verifier registry;
* If identity validation pass, Ocean off-chain component: 
	* retrieve the on-chain checksum of dataset;
	* resolve DID into DDO;
	* extract `list of files` attribute;
	* query checksums of these files from cloud provider such as AWS S3.
* Cloud provider returns the checksums for all files;
* Ocean off-chain component calculates the dataset checksum with formula and compares it against the on-chain checksum;
* If matched, the data availability is verified and data verifier receives the confirmation;
* Otherwise, the data is either changed or unavailable at this time. Verifier will receive the notice of unavailability from the off-chain component.

## 3. Amazon S3 as Storage


### 3.1 Data Attributes 
Amazon S3 provides several different attributes of data, which can be combined to prove that data is the same and available for access. It provides following attributes:

* **ETag**: The entity tag is a hash of the object. The ETag reflects changes only to the contents of an object, not its metadata. 
	* Objects created by the PUT Object, POST Object, or Copy operation, or through the AWS Management Console, and are encrypted by SSE-S3 or plaintext, have ETags that are an MD5 digest of their object data.
	
	* Objects created by the PUT Object, POST Object, or Copy operation, or through the AWS Management Console, and are encrypted by SSE-C or SSE-KMS, have ETags that are not an MD5 digest of their object data.
	
	* If an object is created by either the Multipart Upload or Part Copy operation, the ETag is not an MD5 digest, regardless of the method of encryption.

* **Key**: The dataset name that identifies the data file inside S3 bucket.
* **Size**: The length in bytes of the data.

### 3.2 AWS S3 Experiment

We create a subfolder including a file "subdata.csv" in S3 storage. When the data file is available, S3 should return the metadata information as:

```
 {
            "LastModified": "2019-02-01T00:28:15.000Z", 
            "ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"", 
            "StorageClass": "STANDARD", 
            "Key": "subfolder/", 
            "Owner": {
                "DisplayName": "webaccount", 
                "ID": "a5af246e1a2d8986ddb54302d839152f27823e44e9dc73414037190634ec749c"
            }, 
            "Size": 0
        }, 
        {
            "LastModified": "2019-02-01T00:29:03.000Z", 
            "ETag": "\"997f0517b9e486de9e879e9bd0ae9be1\"", 
            "StorageClass": "STANDARD", 
            "Key": "subfolder/subdata.csv", 
            "Owner": {
                "DisplayName": "webaccount", 
                "ID": "a5af246e1a2d8986ddb54302d839152f27823e44e9dc73414037190634ec749c"
            }, 
            "Size": 41
        }
```

As an experiment, we change a single line in the file "subdata.csv". Then, some information of `subdata.csv` has changed:

* "Size" is changed from 41Bytes to be 40Bytes;
* "ETag" is changed from `997f0517b9e486de9e879e9bd0ae9be1` to be `a0145a3c0f81f2f9e995ccd5024d8e94`.

**Note: ETag of folder remains the same even though the contained files had been modified.**

So, any changes on data file can be detected by comparing the "ETag" against its original records.

```
{
            "LastModified": "2019-02-01T00:28:15.000Z", 
            "ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"", 
            "StorageClass": "STANDARD", 
            "Key": "subfolder/", 
            "Owner": {
                "DisplayName": "webaccount", 
                "ID": "a5af246e1a2d8986ddb54302d839152f27823e44e9dc73414037190634ec749c"
            }, 
            "Size": 0
        }, 
        {
            "LastModified": "2019-02-01T00:44:35.000Z", 
            "ETag": "\"a0145a3c0f81f2f9e995ccd5024d8e94\"", 
            "StorageClass": "STANDARD", 
            "Key": "subfolder/subdata.csv", 
            "Owner": {
                "DisplayName": "webaccount", 
                "ID": "a5af246e1a2d8986ddb54302d839152f27823e44e9dc73414037190634ec749c"
            }, 
            "Size": 40
        }
```

### 3.3 Required File Attributes in DDO

In order to retrieves metadata of a specific file in Amazon S3 without returning the file itself, the [`HEAD OBJECT`](https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectHEAD.html) REST API shall be used. Note API caller must have READ access to the file.


#### 3.3.1 Syntax

To retrieve the metadata including ETag of a file, some information are required:

* ObjectName: the name identifies the file (as shown `Key` field in the above).
* BucketName: the unique name of bucket which includes the file object.
* authorization string: the string used to authorize the read access to the file.

The syntax of request is:

```
HEAD /ObjectName HTTP/1.1
Host: BucketName.s3.amazonaws.com
Authorization: authorization string
Date: date
```

Or 

```
OPTIONS /ObjectName HTTP/1.1
Host: BucketName.s3.amazonaws.com 
Origin: Origin
Access-Control-Request-Method: HTTPMethod
Access-Control-Request-Headers: RequestHeader
```

The following request returns the metadata of a specific file.

* **HEAD Request** Sample: 


	* Sample request:

	```
	HEAD /my-image.jpg HTTP/1.1
	Host: bucket.s3.amazonaws.com
	Date: Wed, 28 Oct 2009 22:32:00 GMT
	Authorization: AWS AKIAIOSFODNN7EXAMPLE:02236Q3V0RonhpaBX5sCYVf1bNRuU=
	```

	* Sample Response

	```
	HTTP/1.1 200 OK
	x-amz-id-2: ef8yU9AS1ed4OpIszj7UDNEHGran
	x-amz-request-id: 318BC8BC143432E5
	x-amz-version-id: 3HL4kqtJlcpXroDTDmjVBH40Nrjfkd
	Date: Wed, 28 Oct 2009 22:32:00 GMT
	Last-Modified: Sun, 1 Jan 2006 12:00:00 GMT
	ETag: "fba9dede5f27731c9771645a39863328"
	Content-Length: 434234
	Content-Type: text/plain
	Connection: close
	Server: AmazonS3
	```

	more details can be found in [HEAD request document](https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectHEAD.html) 

* **OPTIONS Request** Sample:

	* Sample request:

	```
	OPTIONS /exampleobject HTTP/1.1
	Host: examplebucket.s3.amazonaws.com 
	Origin: http://www.example.com
	Access-Control-Request-Method: PUT
	```

	* Sample Response

	```
	HTTP/1.1 200 OK
	x-amz-id-2: 6SvaESv3VULYPLik5LLl7lSPPtSnBvDdGmnklX1HfUl7uS2m1DF6td6KWKNjYMXZ
	x-amz-request-id: BDC4B83DF5096BBE
	Date: Wed, 21 Aug 2012 23:09:55 GMT
	Etag: "1f1a1af1f1111111111111c11aed1da1"
	Access-Control-Allow-Origin: http://www.example.com
	Access-Control-Allow-Methods: PUT
	Access-Control-Expose-Headers: x-amz-request-id
	Content-Length: 0
	Server: AmazonS3
	```



	more details can be found in [OPTIONS request document](https://docs.aws.amazon.com/AmazonS3/latest/API/RESTOPTIONSobject.html)

#### 3.3.2 file attributes stored in DDO

Some file attributes need to be stored in DDO so that Ocean can generate the Requst Query to retrieve checksum of a specific file:

Attribute       |   Type        |   Description |
----------------|---------------|---------------|
ObjectName      |   String      |  filename or "Key" field of metadata. E.g., `data1.csv` & `subfolder/subdata.csv` |
BucketName      |   String      |  bucket name that is unique in S3. |

The `authorization` string can be set as a global environment variable that should not be stored in DDO.



## 4. Microsoft Azure as Storage


### 4.1 Data Attributes 

With Azure, we create a data file that has following attributes:

* **Etag**: It is a fingerprint/checksum of the data file, which can be used to uniquely identify a specific file. The ETag reflects changes only to the name & contents of an file. 

* **name**: The file name that identifies the data inside Azure container.
* **contentLength**: The length in bytes of the contents.

### 4.2 Azure Experiment

The original data file `data.csv` has the Etag as `0x8D68892AED7332B`. 

```
 {
    "content": null,
    "deleted": false,
    "metadata": null,
    "name": "data.csv",
    "properties": {
      ...
      "blobTierInferred": true,
      "blobType": "BlockBlob",
      "contentLength": 40,
      ...
      "creationTime": "2019-02-01T22:14:49+00:00",
      "deletedTime": null,
      "etag": "0x8D68892AED7332B",
      "lastModified": "2019-02-01T22:14:49+00:00",
      ...
      "serverEncrypted": true
    },
    "snapshot": null
  },
```

The Etag becomes `0x8D688972CAF7507` after we modify the data file.

```
{
    "content": null,
    "deleted": false,
    "metadata": null,
    "name": "data.csv",
    "properties": {
      ...
      "blobTierInferred": true,
      "blobType": "BlockBlob",
      "contentLength": 41,
      ...
      "creationTime": "2019-02-01T22:14:49+00:00",
      "deletedTime": null,
      "etag": "0x8D688972CAF7507",
      "lastModified": "2019-02-01T22:46:59+00:00",
      ...
      "serverEncrypted": true
    },
    "snapshot": null
  },
```


### 4.3 Required File Attributes in DDO

In order to retrieves metadata of a specific file in Azure without returning the file itself, the [`Get Blob Properties`](https://docs.microsoft.com/en-us/rest/api/storageservices/Get-Blob-Properties) REST API shall be used depends.


#### 4.3.1 Syntax

To retrieve the metadata including Etag of a file, some information are required:

* BlobName: the name identifies the file (as shown `name` field in the above).
* ContainerName: the unique name of bucket which includes the file object.
* Storage account: name of storage account that is authorized to access the file.

The GET and HEAD operations both retrieve metadata headers for the specified blob. These operations return headers only; they do not return a response body.

The URI syntax for retrieving metadata headers on a blob is as follows:

```
GET/HEAD https://<storageaccount>.blob.core.windows.net/<containername>/<blobname>  
```

* Sample Response

```
Response Status:  
HTTP/1.1 200 OK  

Response Headers:  
x-ms-meta-Name: myblob.txt  
x-ms-meta-DateUploaded: <date>  
x-ms-blob-type: AppendBlob  
x-ms-lease-status: unlocked  
x-ms-lease-state: available  
Content-Length: 11  
Content-Type: text/plain; charset=UTF-8  
Date: <date>  
ETag: "0x8CAE97120C1FF22"  
Accept-Ranges: bytes  
x-ms-blob-committed–block-count: 1  
x-ms-version: 2015-02-21  
Last-Modified: <date>  
Server: Windows-Azure-Blob/1.0 Microsoft-HTTPAPI/2.0  
x-ms-copy-id: 36650d67-05c9-4a24-9a7d-a2213e53caf6  
x-ms-copy-source: <url>  
x-ms-copy-status: success  
x-ms-copy-progress: 11/11  
x-ms-copy-completion-time: <date>  
```

more details can be found in [document](https://docs.microsoft.com/en-us/rest/api/storageservices/Get-Blob-Properties)

#### 4.3.2 file attributes stored in DDO

Some file attributes need to be stored in DDO so that Ocean can generate the Requst Query to retrieve checksum/Etag of a specific file:

Attribute       |   Type        |   Description |
----------------|---------------|---------------|
BlobName        |   String      |  blob name corresponding to data file or "name" field in metadata. E.g., `data.csv`|
ContainerName   |   String      |  container name that contains the data file and is unique in Azure. |



## 5. On-Premise Case

The solution in On-Premise Case is very similar to that in Cloud Provider case. The critical difference is the data provider who serves data on premise should response with Etag header of data file upon request.

### 5.1 Design

Data provider must config a HTTP server, which should interact with Ocean off-chain query component and consumers. To prove the data availability, the HTTP server shall response Ocean's query with Etag header, which is calculated in its local upon query. (Details in [document](https://devcenter.heroku.com/articles/increasing-application-performance-with-http-cache-headers#content-based))

<img src="img/onpremise.jpg" width=1000 />

**Pros:**

* straightforward, implementable and easy to be integrated with Ocean;
* no need to move or modify the data;
* compatible with the workflow using cloud providers (i.e., Amazon S3 and Azure).

**Cons:**

* all parties must trust data provider to be honest. 
* potential attack vector: data provider stores the Etags of files in the cache of HTTP server and returns them upon requst, even though the corresponding files had been removed from local storage.
* it becomes very difficult to detect fraudulence on data provider in this scenario.


### 5.2 file attributes stored in DDO

Some file attributes need to be stored in DDO so that Ocean can generate the Requst Query to retrieve checksum/Etag of a specific file:

Attribute       |   Type        |   Description |
----------------|---------------|---------------|
Name            |   String      | file name. E.g., `data.csv`|
Path            |   String      | relative path of data file in local storage. E.g., `data/volume1` |

The server (i.e., IP & port) and authorization information can be set as environment variables rather than attributes in DDO.


## 6. Reference

* [Amazon S3 REST API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)
* [Azure REST API Reference](https://docs.microsoft.com/en-us/rest/api/storageservices/blob-service-rest-api)
* [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/storage?view=azure-cli-latest)
* [Data Security Privacy Availability and Integrity](http://thesai.org/Downloads/Volume7No4/Paper_64-Data_Security_Privacy_Availability_and_Integrity.pdf)
* [OEP-7 ASSET-DID](https://github.com/oceanprotocol/OEPs/tree/master/7#integrity)
* [OEP-8 ASSET-DDO](https://github.com/oceanprotocol/OEPs/tree/master/8#base-attributes)
* [Increasing Application Performance with HTTP Cache Headers](https://devcenter.heroku.com/articles/increasing-application-performance-with-http-cache-headers#content-based)
* [http cache headers](https://www.keycdn.com/blog/http-cache-headers)

## 7. License

```
Copyright 2018 Ocean Protocol Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

