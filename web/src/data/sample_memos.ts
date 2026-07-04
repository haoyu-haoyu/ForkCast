// One-click sample policy memos for the live-analysis path. These are short
// synthetic consultation notes written for the demo; they are inputs to the
// pipeline, not anchored artifacts.

export interface SampleMemo {
  label: string;
  text: string;
}

export const SAMPLE_MEMOS: SampleMemo[] = [
  {
    label: "Outer-borough parking levy",
    text: "Proposal: introduce a workplace parking levy of £600 per space per year across outer London boroughs from April 2027. Employers with more than 20 spaces would pay; revenue is ring-fenced for bus frequency upgrades and step-free station access. Small businesses, NHS sites and blue-badge spaces are exempt. Council officers expect pushback from retail parks and logistics operators, and support from public-transport advocacy groups. A consultation window of 12 weeks is planned before any charging order is made.",
  },
  {
    label: "School-street car ban pilot",
    text: "Proposal: pilot timed motor-vehicle bans on streets outside 40 primary schools for the autumn term. Cameras would enforce closures 8:15-9:15 and 15:00-16:00 on school days, with resident and disability exemptions. The stated aims are safer crossings, lower NO2 at school gates and higher active-travel rates. Objections are expected from through-traffic commuters and some parents driving from outside the catchment. If casualty and air-quality indicators improve, the scheme would be made permanent and extended to 120 further schools.",
  },
  {
    label: "£15.00 ULEZ variant memo",
    text: "Proposal: raise the ULEZ daily charge for non-compliant vehicles from £12.50 to £15.00 from January 2028, with the scrappage grant increased by £500 for low-income applicants and sole traders. The change is framed as inflation adjustment plus a stronger compliance incentive. Officials anticipate sharper opposition from van-dependent small businesses and outer-borough drivers, alongside continued support from air-quality and public-health groups. Enforcement, exemption and discount structures would otherwise remain unchanged.",
  },
];
