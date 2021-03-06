# Exchange Outlook Connectivity Test
# Cameron Murray (cam@camm.id.au)
#
# You must have a CAS test user creastedbefore using this. To create this
# run .\new-TestCasConnectivityUser.ps1 from the your scripts folder
# under your Exchange Management Installation. Eg:
# C:\Program files\Microsoft\Exchange Server\V14\Scripts
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

Add-PSSnapin Microsoft.Exchange.Management.PowerShell.E2010

$status = 0;
$desc = "";

test-outlookconnectivity -protocol tcp | ForEach-Object {
    if($_.Result -like "Success") {
        
    } elseif($_.Result -like "Failure") {
        $desc="Outlook Connectivity Failure " + $_.Scenario;
        $status=2;
    } else {
        # Somethings up..
        $status=2;
        $desc="Unknown Failure"
    }
}

if ($status -eq "2") {
	Write-Host "CRITICAL: " + $desc
} elseif ($status -eq "0") {
	Write-Host "OK: Outlook Connectivity OK"
} 

exit $status;