terraform {
  backend "s3" {
    bucket = "sctp-tfstate-ce13"
    key    = "tk/tf-coaching-16-bootstrap.tfstate"
    #use_lockfile = true
    region = "us-east-1"
  }
}