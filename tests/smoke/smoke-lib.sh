#!/bin/bash
# PURPOSE:    Routines to make writing smoke tests easier
#
# NOTES:
#   Generally the functions here try to make it easy to compare
#   current program output with past program output.  Its up to you to
#   make sure that some particular output is "right".  In this
#   context,  "output" can be one or more of the following:
#      - Output from a command: (stdout)
#      - Error from a command: (stderr, generaly should be empty)
#      - Data files written by a command.
#
#
# AUTHORS:    S. Pothier
##############################################################################

sto="$HOME/.smoke-test-output"
mkdir -p $sto > /dev/null

# Default counters if something didn't previously set them
x=${failcnt:=0} 
x=${totalcnt:=0}


function testIrods () {
  proc=testIrods
  testName="$1" # No Spaces; e.g. CCUE
  HDR="$2"
  expectedStatus=${3:-4} # default, HDR not found in iRODS
  /usr/local/share/applications/irods3.3.1/iRODS/clients/icommands/bin/ils $HDR > /dev/null 2>&1
  actualStatus=$?
  if [ $actualStatus -ne $expectedStatus ]; then
    echo "Failed command: ${HDR} found using ils"
    echo "*** $proc FAILED [$testName] (Command returned unexpected status; got $actualStatus <> $expectedStatus) ***"
    failcnt=$((failcnt + 1))
    return_code=1
  else
    echo "*** $proc PASSED [$testName] (Command correctly returned status = $expectedStatus)***"
  fi
}

##
## Run given CMD and compare its ACTUAL stdout to EXPECTED stdout.
## Ignore lines that start with COMMENT (defaults to ";")
##
function testCommand () {
  proc=testCommand
  testName="$1" # No Spaces; e.g. CCUE
  CMD="$2"
  COMMENT=${3:-"^;"}
  displayOutputP=${4:-"y"}      # or "n" to save stdout to file only
  expectedStatus=${5:-0}

  totalcnt=$((totalcnt + 1))
  actual="${testName}.out"
  err="${testName}.err"
  GOLD="${actual}.GOLD"
  diff="diff.out"

  # This isn't a great solution since it only works with bash, but it gets
  # me by.
  # 
  # The PIPESTATUS is a special bash variable which is an array.  Since I
  # didn't give a subscript, I got the first element which is what I
  # wanted.

  #! echo "EXECUTING: $cmd"
  tn="1/3"
  if [ "y" = "$displayOutputP" ]; then
    eval ${CMD} 2> $sto/$err | tee $sto/$actual
  else
    eval ${CMD} 2> $sto/$err > $sto/$actual
  fi
  actualStatus=$PIPESTATUS
  if [ $actualStatus -ne $expectedStatus ]; then
    echo "Failed command: ${CMD}"
    echo "*** $proc FAILED [$testName] ($tn; Command returned unexpected status; got $actualStatus <> $expectedStatus) ***"
    failcnt=$((failcnt + 1))
    return_code=1
  else
    echo "*** $proc PASSED [$testName] ($tn; Command correctly returned status = $expectedStatus***"
  fi
  ## Make sure we didn't get errors (output to stderr).
  tn="2/3"
  if [ -s $err ]; then
    cat $err
    echo "*** $proc FAILED [$testName] ($tn; Output was sent to STDERR: $err) ***"
    failcnt=$((failcnt + 1))
    return_code=1
  else
    echo "*** $proc PASSED [$testName] ($tn; no STDERR output) ***"
    #!rm $err
  fi

  # filter out diagnostic output (if any)
  #! echo "DEBUG: COMMENT=${COMMENT}"
  egrep -v ${COMMENT} $sto/$actual > $sto/$actual.clean
  egrep -v ${COMMENT} $GOLD > $sto/$GOLD.clean

  tn="3/3"
  if ! diff $sto/$GOLD.clean $sto/$actual.clean > $sto/$diff;  then
      cat $sto/$diff
      pwd=`pwd`
      echo ""
      echo "To accept current results: cp $sto/$actual $pwd/$GOLD"
      echo "*** $proc FAILED [$testName] ($tn; got UNEXPECTED STDOUT) ***"
      failcnt=$((failcnt + 1))
      return_code=1
  else
      echo "*** $proc PASSED [$testName] ($tn; got expected STDOUT) ***"
      #!rm $diff $GOLD.clean $sto/$actual.clean
  fi
}  # END testCommand


##
## Make sure a generated output file matches expected.
## Ignore lines that match regular expression VARIANT (defaults to "^;")
##
function testOutput () { 
  proc=testOutput
  testName="$1" # No Spaces; e.g. CCUE
  output=$2
  GOLD=${output}.GOLD

  VARIANT=${3:-"^;"}
  displayOutputP=${4:-"y"}      # or "n" to save stdout to file only
  diff="${output}.diff"
  totalcnt=$((totalcnt + 1))
  
  if [ ! -f $GOLD ]; then
      pwd=`pwd`
      echo "Could not find: $GOLD"
      echo "To accept current output: cp $output $pwd/$GOLD"
      failcnt=$((failcnt + 1))
      return_code=2
  fi

  # filter out diagnostic output (if any)
  egrep -v "${VARIANT}" $output > $sto/$output.clean
  egrep -v "${VARIANT}" $GOLD > $sto/$GOLD.clean

  if ! diff $sto/$GOLD.clean $sto/$output.clean > $sto/$diff;  then
      if [ "y" = "$displayOutputP" ]; then
          cat $sto/$diff
      else
          echo ""
          echo "[$testName] DIFF between ACTUAL and EXPECTED output is in: "
          echo "  $sto/$diff"
          echo ""
      fi
      pwd=`pwd`
      echo ""
      echo "To accept current results: cp $pwd/$output $pwd/$GOLD"
      echo "*** $proc  FAILED  [$testName] (got UNEXPECTED output in: $output) ***"
      failcnt=$((failcnt + 1))
      return_code=1
  else
      echo "*** $proc  PASSED [$testName] (got expected output in: $output) ***"
      #!rm $diff $GOLD.clean $output.clean
  fi
}

##
## Make sure log file contains what we expect
##
function testLog () {
    local testName="$1" # No Spaces; e.g. CCUE
    local filter="$2"
    local output="${testName}.out"
    local GOLD="${output}.GOLD"
    local proc="testLog"
    local displayOutputP="y"      # or "n" to save stdout to file only
    local diff="${output}.diff"

    totalcnt=$((totalcnt + 1))

    if [ ! -f $GOLD ]; then
	pwd=`pwd`
	echo "Could not find: $GOLD"
	echo "To accept current output: cp $output $pwd/$GOLD"
	failcnt=$((failcnt + 1))
	return_code=2
    fi

    eval "${filter}" > $sto/$output

    if ! diff $GOLD $sto/$output > $sto/$diff;  then
	if [ "y" = "$displayOutputP" ]; then
            cat $sto/$diff
	else
            echo ""
            echo "[$testName] DIFF between ACTUAL and EXPECTED output is in: "
            echo "  $sto/$diff"
            echo ""
	fi
	pwd=`pwd`
	echo ""
	echo "To accept current results: cp $sto/$output $pwd/$GOLD"
	echo "*** $proc  FAILED  [$testName] (got UNEXPECTED output in: $output) ***"
	failcnt=$((failcnt + 1))
	return_code=1
    else
	echo "*** $proc  PASSED [$testName] (got expected output in: $output) ***"
    fi
    
}

##############################################################################
