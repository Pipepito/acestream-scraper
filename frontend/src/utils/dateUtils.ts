const padDatePart = (value: number) => value.toString().padStart(2, '0');

export const getLocalISODate = (date = new Date()) => {
  const year = date.getFullYear();
  const month = padDatePart(date.getMonth() + 1);
  const day = padDatePart(date.getDate());

  return `${year}-${month}-${day}`;
};

export const getRelativeLocalISODate = (daysOffset: number, baseDate = new Date()) => {
  const nextDate = new Date(baseDate);
  nextDate.setDate(nextDate.getDate() + daysOffset);

  return getLocalISODate(nextDate);
};
