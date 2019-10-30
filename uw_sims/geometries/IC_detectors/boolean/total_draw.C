void total_draw()
// Example simple postprocessing in root: plot spectra of total Edep (>0) in each TubeVol 
{
  //gStyle->SetOptStat(0);
  //gStyle->SetOptTitle(0);

  TFile* file = TFile::Open("total_out.root");
 

  TCanvas* c1 = new TCanvas("c1","c1", 0,0,900,800);	
  c1->cd();
  c1->SetLogy();
  TH1D* histo_energy= new TH1D ("histo_energy", "histo_energy", 1000, 0, 2.65); 
  histo_energy->SetLineColor(kRed);
  histo_energy->SetXTitle("energy [MeV]");
  histo_energy->SetYTitle("counts");

  TTree* tree = (TTree*) file->Get("g4sntuple");
 
  vector<double> *energy_hit = new vector<double> (1000);
  int nEvents=0;
  int entries= tree->GetEntries();
  tree->SetBranchAddress("Edep", &energy_hit);
  tree->SetBranchAddress("nEvents", &nEvents);
  for (int i=0; i<entries; i++){
	tree->GetEntry(i);
	double total_energy=0;
	for (int j=0; j<nEvents; j++){
	total_energy+=energy_hit->at(j);
	}
	histo_energy->Fill(total_energy);
  }

histo_energy->Draw();

/*
  TLegend* legend = new TLegend(0.15, 0.7, 0.3, 0.85);
  legend->SetBorderSize(0);
  legend->AddEntry(histo_energy, "detector 1", "L");
  legend->AddEntry(tree, "detector 2", "L");
  legend->Draw();
*/


  TCanvas* c2 = new TCanvas("c2","c2", 0,0,900,800);
  c2->cd();
  c2->SetLogy();
  tree->Draw("KE >> histo_k(1000,0,2.65)");
  TH1D* histo_k= (TH1D*)gDirectory->Get("histo_k");
  histo_k->SetLineColor(kRed);

}

