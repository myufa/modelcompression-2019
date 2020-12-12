#include <fstream>
#include <string>

using namespace std;

int main() {
    ifstream input("validate.txt");
    ofstream output("validateNEW.txt");
    string line;

    

    while (getline(input, line)) {
        // line = /mnt/d/Documents/CourseWork/F2020/eecs442/final/PyTorch-YOLOv3/data/coco/images/train2014/SOMEFILENAME
        //         // need to replace PyTorch-YOLOv3 w/ modelcompression-2019
        string post = line.substr(13, string::npos);
        output << "/scratch/robosub_team_root/robosub_team/shared_data/" + post + "\n";
    }
}
